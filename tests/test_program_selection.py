"""Exercise category selection, restore and Start using real HA dispatching."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.candy.const import (
    DATA_KEY_WM_CATEGORY, DATA_KEY_WM_SPIN, DATA_KEY_WM_TEMP,
    SIGNAL_WM_PROGRAM_CHANGED,
)
from custom_components.candy.select import (
    CandyWashProgramSelect, CandyWashTemperatureSelect, CandyWashSpinSelect,
    _WM_PROGRAMS_BY_CATEGORY,
)
from custom_components.candy.wash_settings import select_wash_program


def entity(cls, hass, data):
    instance = cls("test", data, SimpleNamespace(last_update_success=True))
    instance.hass = hass
    instance.async_write_ha_state = MagicMock()
    return instance


async def test_category_change_resets_settings_and_notifies_controls(hass):
    data = {}
    select_wash_program(data, "Trainers")
    data.update(wm_temp=90, wm_spin=15, wm_steam=2, wm_soil=3)
    program = entity(CandyWashProgramSelect, hass, data)
    program._current_option = "Trainers"
    callback = MagicMock()
    unsub = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), callback)
    try:
        category = next(cat for cat, names in _WM_PROGRAMS_BY_CATEGORY.items() if "Trainers" not in names)
        data[DATA_KEY_WM_CATEGORY] = category
        program._on_category_changed(category)
        await hass.async_block_till_done()
        assert data["wm_program_name"] == program.current_option
        assert data["wm_temp"] != 90
        callback.assert_called_once()
    finally:
        unsub()


async def test_direct_recipe_selection_updates_controls(hass):
    data = {}
    program = entity(CandyWashProgramSelect, hass, data)
    temp = entity(CandyWashTemperatureSelect, hass, data)
    spin = entity(CandyWashSpinSelect, hass, data)
    unsub_temp = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), temp._on_program_changed)
    unsub_spin = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), spin._on_program_changed)
    try:
        await program.async_select_option("Trainers")
        await hass.async_block_till_done()
        assert temp.current_option == "20°C"
        assert spin.current_option == "400 rpm"
        with pytest.raises(HomeAssistantError):
            await spin.async_select_option("1500 rpm")
        assert data[DATA_KEY_WM_SPIN] == 4
    finally:
        unsub_temp()
        unsub_spin()


async def test_missing_temperature_default_is_not_changed_to_40(hass):
    data = {}
    select_wash_program(data, "Perfect 20")
    temp = entity(CandyWashTemperatureSelect, hass, data)
    from custom_components.candy.programs import WASHING_MACHINE_PROGRAMS_BY_NAME
    temp._on_program_changed(WASHING_MACHINE_PROGRAMS_BY_NAME["Perfect 20"])
    assert temp.current_option == "Program default"
    assert data[DATA_KEY_WM_TEMP] is None


async def test_every_catalogue_spin_default_survives_display_roundtrip(hass):
    from custom_components.candy.programs import WASHING_MACHINE_PROGRAMS
    for recipe in WASHING_MACHINE_PROGRAMS:
        data = {}
        select_wash_program(data, recipe.name)
        spin = entity(CandyWashSpinSelect, hass, data)
        spin._on_program_changed(recipe)
        assert data[DATA_KEY_WM_SPIN] == recipe.spin_target, recipe.name


async def test_start_sends_selected_recipe_and_refreshes(hass):
    import json
    from pathlib import Path
    from custom_components.candy.button import CandyWashStartButton
    from custom_components.candy.client.model import WashingMachineStatus
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/idle.json"
    status = WashingMachineStatus.from_json(json.loads(fixture.read_text())["statusLavatrice"])
    coordinator = MagicMock()
    coordinator.data = status
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    from custom_components.candy.client.model import MachineState
    def report_running():
        status.machine_state = MachineState.RUNNING
    coordinator.async_request_refresh.side_effect = report_running
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock())
    data = {}
    select_wash_program(data, "Trainers")
    start = CandyWashStartButton(coordinator, client, "test", data, hass)
    with patch("custom_components.candy.button.asyncio.sleep", new_callable=AsyncMock):
        await start.async_press()
    payload = client.send_plaintext.await_args.args[0]
    assert "Sel=93&PrNm=11" in payload
    assert "TmpTgt=20" in payload
    assert "SpdTgt=4" in payload
    assert client.write_pending is False
    assert data["last_requested_program"] == "Trainers"
    assert data["last_start"]["result"] == "running_recipe_unverified"
    assert data["last_start"]["recipe_confirmed"] is False
    coordinator.async_request_refresh.assert_awaited_once()


async def test_start_rejects_remote_control_disabled(hass):
    import json
    from pathlib import Path
    from custom_components.candy.button import CandyWashStartButton
    from custom_components.candy.client.model import WashingMachineStatus
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/idle.json"
    status = WashingMachineStatus.from_json(json.loads(fixture.read_text())["statusLavatrice"])
    status.remote_control = False
    coordinator = MagicMock()
    coordinator.data = status
    coordinator.last_update_success = True
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock())
    data = {}
    select_wash_program(data, "Trainers")
    start = CandyWashStartButton(coordinator, client, "test", data, hass)
    with pytest.raises(HomeAssistantError):
        await start.async_press()
    client.send_plaintext.assert_not_awaited()


async def test_integration_registers_controls_and_reports_device_codes(hass, aioclient_mock):
    """Use registry identities, independent of translated names and entity IDs."""
    from pathlib import Path
    from homeassistant.helpers import entity_registry as er
    from custom_components.candy.const import DOMAIN
    from .common import init_integration
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/running_wash.json"
    await init_integration(hass, aioclient_mock, fixture.read_text())
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    registry = er.async_get(hass)
    for platform, suffix in [
        ("select", "s02_wm_program"), ("button", "wash_start_button"),
        ("binary_sensor", "wm_remote_control"), ("sensor", "wm_program_sensor"),
    ]:
        entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}-{suffix}")
        assert entity_id is not None, suffix
        state = hass.states.get(entity_id)
        assert state is not None, suffix
        if suffix == "wm_program_sensor":
            assert state.state.startswith(("PrNm ", "Pr "))
            assert state.attributes["recipe_name_confirmed"] is False


async def test_http_success_but_panel_stays_ready_is_not_confirmed(hass):
    import json
    from pathlib import Path
    from custom_components.candy.button import CandyWashStartButton, StartNotConfirmed
    from custom_components.candy.client.model import WashingMachineStatus
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/idle.json"
    status = WashingMachineStatus.from_json(json.loads(fixture.read_text())["statusLavatrice"])
    status.temp = 40
    status.spin_speed = 1000
    coordinator = MagicMock()
    coordinator.data = status
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock(return_value="OK"))
    data = {}
    select_wash_program(data, "Trainers")
    start = CandyWashStartButton(coordinator, client, "test", data, hass)
    with patch("custom_components.candy.button.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(StartNotConfirmed):
            await start.async_press()
    client.send_plaintext.assert_awaited_once()
    assert coordinator.async_request_refresh.await_count == 3
    assert client.write_pending is False
    assert data["last_start"]["result"] == "not_confirmed"
    assert data["last_start"]["after"]["temperature"] == 40
    assert data["last_start"]["after"]["spin_rpm"] == 1000
    assert "last_requested_program" not in data


async def test_rejected_command_unlocks_buttons_and_records_failure(hass):
    import json
    from pathlib import Path
    from custom_components.candy.button import CandyWashStartButton
    from custom_components.candy.client.model import WashingMachineStatus
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/idle.json"
    status = WashingMachineStatus.from_json(json.loads(fixture.read_text())["statusLavatrice"])
    coordinator = MagicMock()
    coordinator.data = status
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock(side_effect=ValueError("Rejected")))
    data = {}
    select_wash_program(data, "Trainers")
    start = CandyWashStartButton(coordinator, client, "test", data, hass)
    with pytest.raises(ValueError):
        await start.async_press()
    assert data["last_start"]["result"] == "send_failed"
    assert client.write_pending is False
    client.send_plaintext.assert_awaited_once()


async def test_downloaded_diagnostics_exclude_config_secrets(hass):
    from custom_components.candy.diagnostics import async_get_config_entry_diagnostics
    from custom_components.candy.const import DOMAIN, DATA_KEY_COORDINATOR
    coordinator = SimpleNamespace(data=None, last_update_success=False)
    hass.data.setdefault(DOMAIN, {})["test"] = {DATA_KEY_COORDINATOR: coordinator}
    entry = SimpleNamespace(entry_id="test", data={"password":"private", "ip_address":"192.0.2.1"})
    diagnostic = await async_get_config_entry_diagnostics(hass, entry)
    assert "private" not in str(diagnostic)
    assert "192.0.2.1" not in str(diagnostic)
