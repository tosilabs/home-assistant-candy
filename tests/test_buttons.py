"""Exercise actual registered buttons in valid machine states."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import load_fixture

from .common import init_integration, registered_entity_id


@pytest.mark.parametrize("kind,prefix", [("washing_machine", "wash"), ("tumble_dryer", "tumble")])
async def test_control_buttons_created(hass, aioclient_mock, kind, prefix):
    await init_integration(hass, aioclient_mock, load_fixture(f"{kind}/idle.json"))
    for action in ("start", "pause", "resume", "stop"):
        entity_id = registered_entity_id(hass, "button", f"{prefix}_{action}_button")
        assert hass.states.get(entity_id) is not None


@pytest.mark.parametrize("kind,action,machine_state,expected", [
    ("washing_machine", "pause", "2", "Write=1&Pa=1"),
    ("washing_machine", "resume", "3", "Write=1&Pa=0"),
    ("washing_machine", "stop", "2", "Write=1&StSt=0&DelMd=0&PrNm=1"),
    ("tumble_dryer", "pause", "2", "Write=1&Pa=1"),
])
async def test_control_sends_captured_plaintext(hass, aioclient_mock, kind, action, machine_state, expected):
    fixture = json.loads(load_fixture(f"{kind}/idle.json"))
    if kind == "washing_machine":
        fixture["statusLavatrice"].update(MachMd=machine_state, PrNm="1")
        prefix = "wash"
    else:
        fixture["statusTD"]["StatoTD"] = machine_state
        prefix = "tumble"
    await init_integration(hass, aioclient_mock, json.dumps(fixture))
    entity_id = registered_entity_id(hass, "button", f"{prefix}_{action}_button")
    with patch("custom_components.candy.client.CandyClient.send_plaintext", new_callable=AsyncMock) as send, \
         patch("custom_components.candy.button.asyncio.sleep", new_callable=AsyncMock):
        await hass.services.async_call("button", "press", {"entity_id": entity_id}, blocking=True)
    send.assert_awaited_once_with(expected)
