"""Exercise grouped selection, restore and Start using real HA dispatching."""
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
)
from custom_components.candy.wash_settings import select_wash_program


def entity(cls, hass, data):
    instance = cls("test", data, SimpleNamespace(last_update_success=True))
    instance.hass = hass
    instance.async_write_ha_state = MagicMock()
    return instance


async def test_grouped_options_ignore_retired_category_filter(hass):
    data = {DATA_KEY_WM_CATEGORY: "Cycles"}
    program = entity(CandyWashProgramSelect, hass, data)
    await program.async_select_option("Sport & Leisure - Trainers")
    assert program.current_option == "Sport & Leisure - Trainers"
    assert data["wm_program_name"] == "Trainers"
    assert program.extra_state_attributes["program_name"] == "Trainers"
    assert program.extra_state_attributes["description_sq"]
    assert len(program.options) == 71


@pytest.mark.parametrize("saved,attrs", [
    ("Trainers", {}),
    ("Sport & Leisure - Trainers", {}),
    ("Old category - Trainers", {"program_name": "Trainers"}),
])
async def test_restore_keeps_recipe_identity(hass, saved, attrs):
    from homeassistant.core import State
    program = entity(CandyWashProgramSelect, hass, {})
    program.async_get_last_state = AsyncMock(return_value=State("select.test", saved, attrs))
    with patch("custom_components.candy.select._CandySelectBase.async_added_to_hass", new_callable=AsyncMock):
        await program.async_added_to_hass()
    assert program.current_option == "Sport & Leisure - Trainers"
    assert program._entry_data["wm_temp"] == 20
    assert program._entry_data["wm_spin"] == 4


async def test_direct_recipe_selection_updates_controls(hass):
    data = {}
    program = entity(CandyWashProgramSelect, hass, data)
    temp = entity(CandyWashTemperatureSelect, hass, data)
    spin = entity(CandyWashSpinSelect, hass, data)
    unsub_temp = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), temp._on_program_changed)
    unsub_spin = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), spin._on_program_changed)
    try:
        await program.async_select_option("Sport & Leisure - Trainers")
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
    program = entity(CandyWashProgramSelect, hass, data)
    await program.async_select_option("Sport & Leisure - Trainers")
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


async def test_grouped_select_service_and_retired_category_migration(hass, aioclient_mock):
    from pathlib import Path
    from homeassistant.helpers import entity_registry as er
    from custom_components.candy.const import DOMAIN
    from .common import init_integration, registered_entity_id
    fixture = Path(__file__).parent / "components/washing_machine/fixtures/idle.json"
    await init_integration(hass, aioclient_mock, fixture.read_text())
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    registry = er.async_get(hass)
    old = registry.async_get_or_create("select", DOMAIN,
        f"{entry.entry_id}-s01_wm_category", config_entry=entry,
        suggested_object_id="old_category")
    program_id = registered_entity_id(hass, "select", "s02_wm_program")
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(old.entity_id).disabled_by == er.RegistryEntryDisabler.INTEGRATION
    assert registered_entity_id(hass, "select", "s02_wm_program") == program_id
    await hass.services.async_call("select", "select_option", {
        "entity_id": program_id, "option": "Sport & Leisure - Trainers",
    }, blocking=True)
    assert hass.states.get(program_id).state == "Sport & Leisure - Trainers"
    assert hass.data[DOMAIN][entry.entry_id]["wm_program_name"] == "Trainers"


async def test_dryer_start_resolves_grouped_label_without_changing_command(hass):
    from homeassistant.helpers import entity_registry as er
    from custom_components.candy.const import DOMAIN
    from custom_components.candy.select import CandyTumbleProgramSelect, UNIQUE_ID_TD_PROGRAM_SELECT
    from custom_components.candy.button import CandyTumbleStartButton
    from custom_components.candy.programs import TUMBLE_DRYER_PROGRAMS_BY_NAME
    from custom_components.candy.client.commands import tumble_dryer_start
    data = {}
    program = entity(CandyTumbleProgramSelect, hass, data)
    await program.async_select_option("Sport & Leisure - Backpacks")
    registry = er.async_get(hass)
    registered = registry.async_get_or_create("select", DOMAIN, UNIQUE_ID_TD_PROGRAM_SELECT.format("test"))
    hass.states.async_set(registered.entity_id, program.current_option)
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock())
    start = CandyTumbleStartButton(MagicMock(), client, "test", data, hass)
    start._send_and_refresh = AsyncMock()
    await start.async_press()
    recipe = TUMBLE_DRYER_PROGRAMS_BY_NAME["Backpacks"]
    start._send_and_refresh.assert_awaited_once_with(tumble_dryer_start(
        program=recipe.program, time=recipe.time, opt_mask=recipe.opt_mask,
        dry_level=recipe.dry_level, selection=recipe.selection,
        rapid=recipe.rapid, pr_str=recipe.name,
    ))
