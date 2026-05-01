"""Tests for the Candy button platform and command services."""
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import \
    AiohttpClientMocker

from custom_components.candy.const import (ATTR_PARAMS, DOMAIN, SERVICE_PAUSE,
                                           SERVICE_RESUME, SERVICE_SEND_COMMAND)

from .common import TEST_IP, init_integration


async def _setup_and_get_entry_id(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> str:
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    return entries[0].entry_id


async def test_pause_button_press(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    aioclient_mock.get(f"http://{TEST_IP}/http-write.json", text="OK")

    state = hass.states.get("button.pause")
    assert state is not None

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.pause"}, blocking=True
    )

    write_calls = [c for c in aioclient_mock.mock_calls if "/http-write.json" in str(c[1])]
    assert len(write_calls) == 1
    query = dict(write_calls[0][1].query)
    assert query["Pause"] == "1"
    assert query["WiFiStatus"] == "1"


async def test_resume_button_press(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    aioclient_mock.get(f"http://{TEST_IP}/http-write.json", text="OK")

    state = hass.states.get("button.resume")
    assert state is not None

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.resume"}, blocking=True
    )

    write_calls = [c for c in aioclient_mock.mock_calls if "/http-write.json" in str(c[1])]
    assert len(write_calls) == 1
    query = dict(write_calls[0][1].query)
    assert query["Pause"] == "0"
    assert query["WiFiStatus"] == "1"


async def test_send_command_service(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    entry_id = await _setup_and_get_entry_id(hass, aioclient_mock)

    aioclient_mock.get(f"http://{TEST_IP}/http-write.json", text="OK")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        {
            "entry_id": entry_id,
            ATTR_PARAMS: {"WashProgr": 13, "Temp": 40, "WiFiStatus": 1},
        },
        blocking=True,
    )

    write_calls = [c for c in aioclient_mock.mock_calls if "/http-write.json" in str(c[1])]
    assert len(write_calls) == 1
    query = dict(write_calls[0][1].query)
    assert query["WashProgr"] == "13"
    assert query["Temp"] == "40"
    assert query["WiFiStatus"] == "1"


async def test_pause_resume_services(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    entry_id = await _setup_and_get_entry_id(hass, aioclient_mock)

    aioclient_mock.get(f"http://{TEST_IP}/http-write.json", text="OK")

    await hass.services.async_call(
        DOMAIN, SERVICE_PAUSE, {"entry_id": entry_id}, blocking=True
    )
    await hass.services.async_call(
        DOMAIN, SERVICE_RESUME, {"entry_id": entry_id}, blocking=True
    )

    write_calls = [c for c in aioclient_mock.mock_calls if "/http-write.json" in str(c[1])]
    assert len(write_calls) == 2
    assert dict(write_calls[0][1].query)["Pause"] == "1"
    assert dict(write_calls[1][1].query)["Pause"] == "0"
