"""The cancel/prepare button must never start a wash or guess an active program."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.candy.button import CandyWashPrepareButton, CandyWashStartButton
from custom_components.candy.client.model import WashingMachineStatus, MachineState, WashProgramState
from custom_components.candy.wash_settings import select_wash_program


def controls(hass, state=MachineState.RUNNING, program=4):
    raw = json.loads((Path(__file__).parent / "components/washing_machine/fixtures/idle.json").read_text())
    status = WashingMachineStatus.from_json(raw["statusLavatrice"])
    status.machine_state = state
    status.program = program
    status.program_state = WashProgramState.WASH if state == MachineState.RUNNING else WashProgramState.STOPPED
    coordinator = MagicMock(data=status, last_update_success=True)
    coordinator.async_request_refresh = AsyncMock()
    client = SimpleNamespace(write_pending=False, send_plaintext=AsyncMock())
    data = {}
    select_wash_program(data, "Trainers")
    data.update(wm_temp=90, wm_spin=15, wm_steam=2, wm_soil=3)
    button = CandyWashPrepareButton(coordinator, client, "test", data)
    button.hass = hass
    return button, coordinator, client, data


async def test_cancels_fresh_current_program_then_resets_trainers(hass):
    button, coordinator, client, data = controls(hass)
    reads = 0
    def refresh():
        nonlocal reads
        reads += 1
        if reads == 1:
            coordinator.data.program = 8  # Device changed since cached status.
        else:
            coordinator.data.machine_state = MachineState.IDLE
            coordinator.data.program_state = WashProgramState.STOPPED
    coordinator.async_request_refresh.side_effect = refresh
    with patch("custom_components.candy.button.asyncio.sleep", new_callable=AsyncMock):
        await button.async_press()
    client.send_plaintext.assert_awaited_once_with("Write=1&StSt=0&DelMd=0&PrNm=8")
    assert data["last_prepare"]["result"] == "ready"
    assert data["wm_temp"] == 20
    assert data["wm_spin"] == 4
    assert data["wm_steam"] == 0
    assert data["wm_soil"] is None
    assert client.write_pending is False


async def test_unconfirmed_stop_blocks_start_and_never_retries_write(hass):
    button, coordinator, client, data = controls(hass)
    with patch("custom_components.candy.button.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(HomeAssistantError, match="not confirmed"):
            await button.async_press()
    client.send_plaintext.assert_awaited_once()
    assert coordinator.async_request_refresh.await_count == 4
    assert data["last_prepare"]["result"] == "not_confirmed"
    coordinator.data.machine_state = MachineState.IDLE
    start = CandyWashStartButton(coordinator, client, "test", data, hass)
    assert start.available is False
    assert client.write_pending is False


async def test_unknown_active_program_is_not_guessed_from_trainers_or_previous_start(hass):
    button, coordinator, client, data = controls(hass, program=None)
    data["last_program"] = 11
    with pytest.raises(HomeAssistantError, match="unknown"):
        await button.async_press()
    client.send_plaintext.assert_not_awaited()
    assert data["last_prepare"]["result"] == "failed"
    assert client.write_pending is False


async def test_already_ready_without_program_only_resets_local_settings(hass):
    button, coordinator, client, data = controls(hass, MachineState.IDLE, None)
    await button.async_press()
    client.send_plaintext.assert_not_awaited()
    assert data["last_prepare"]["result"] == "ready"
    assert data["wm_temp"] == 20


async def test_stale_status_cannot_confirm_preparation(hass):
    button, coordinator, client, data = controls(hass)
    coordinator.async_request_refresh.side_effect = lambda: setattr(coordinator, "last_update_success", False)
    with pytest.raises(HomeAssistantError, match="unavailable"):
        await button.async_press()
    client.send_plaintext.assert_not_awaited()
    assert client.write_pending is False


async def test_prepare_preserves_lock_and_releases_after_transport_failure(hass):
    button, coordinator, client, data = controls(hass)
    async def fail_send(_command):
        assert client.write_pending is True
        raise ValueError("Rejected")
    client.send_plaintext.side_effect = fail_send
    with pytest.raises(ValueError):
        await button.async_press()
    assert client.write_pending is False
    assert data["last_prepare"]["result"] == "failed"
