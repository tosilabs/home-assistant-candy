"""Tests for button entities (Pause / Resume / Stop)."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import \
    AiohttpClientMocker

from .common import init_integration


async def test_washing_machine_buttons_created(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    assert hass.states.get("button.pause_washing_machine") is not None
    assert hass.states.get("button.resume_washing_machine") is not None
    assert hass.states.get("button.stop_washing_machine") is not None


async def test_tumble_dryer_buttons_created(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("tumble_dryer/running.json"))

    assert hass.states.get("button.pause_tumble_dryer") is not None
    assert hass.states.get("button.resume_tumble_dryer") is not None
    assert hass.states.get("button.stop_tumble_dryer") is not None


async def test_wm_pause_button_sends_correct_plaintext(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    with patch("custom_components.candy.client.CandyClient.encrypt_command", return_value="DEADBEEF") as mock_enc, \
         patch("custom_components.candy.client.CandyClient.send_encrypted_data", new_callable=AsyncMock) as mock_send:
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.pause_washing_machine"}, blocking=True
        )

    mock_enc.assert_called_once_with("Write=1&Pa=1")
    mock_send.assert_called_once_with("DEADBEEF")


async def test_wm_resume_button_sends_correct_plaintext(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    with patch("custom_components.candy.client.CandyClient.encrypt_command", return_value="00") as mock_enc, \
         patch("custom_components.candy.client.CandyClient.send_encrypted_data", new_callable=AsyncMock):
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.resume_washing_machine"}, blocking=True
        )

    mock_enc.assert_called_once_with("Write=1&Pa=0")


async def test_wm_stop_button_uses_current_program(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    # idle.json reports program=1
    await init_integration(hass, aioclient_mock, load_fixture("washing_machine/idle.json"))

    with patch("custom_components.candy.client.CandyClient.encrypt_command", return_value="00") as mock_enc, \
         patch("custom_components.candy.client.CandyClient.send_encrypted_data", new_callable=AsyncMock):
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.stop_washing_machine"}, blocking=True
        )

    mock_enc.assert_called_once_with("Write=1&StSt=0&DelMd=0&PrNm=1")


async def test_td_pause_button_sends_correct_plaintext(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    await init_integration(hass, aioclient_mock, load_fixture("tumble_dryer/running.json"))

    with patch("custom_components.candy.client.CandyClient.encrypt_command", return_value="00") as mock_enc, \
         patch("custom_components.candy.client.CandyClient.send_encrypted_data", new_callable=AsyncMock):
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.pause_tumble_dryer"}, blocking=True
        )

    mock_enc.assert_called_once_with("Write=1&Pa=1")
