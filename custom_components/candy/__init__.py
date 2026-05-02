"""The Candy integration."""
from __future__ import annotations

import logging
import re
from datetime import timedelta

import async_timeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .client import CandyClient
from .client.commands import (tumble_dryer_pause, tumble_dryer_resume,
                              tumble_dryer_start, tumble_dryer_stop,
                              washing_machine_pause, washing_machine_resume,
                              washing_machine_start, washing_machine_stop)
from .client.model import TumbleDryerStatus, WashingMachineStatus

from .const import *

_LOGGER = logging.getLogger(__name__)

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def _hex_string(value: object) -> str:
    s = cv.string(value).strip()
    if len(s) % 2 != 0 or not _HEX_RE.match(s):
        raise vol.Invalid("data must be an even-length hex string")
    return s


SEND_COMMAND_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_PARAMS): vol.Schema({cv.string: vol.Any(cv.string, int)}),
})

SEND_RAW_COMMAND_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_DATA): _hex_string,
})

SEND_PLAINTEXT_COMMAND_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_PLAINTEXT): cv.string,
})

DECRYPT_DATA_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_DATA): _hex_string,
})

WM_START_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_TEMP): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SPIN_TARGET): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SPIN_DEFAULT): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SOIL_LEVEL): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_STEAM, default=0): vol.All(int, vol.Range(min=0, max=1)),
})

WM_STOP_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Optional(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
})

TD_START_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_DRY_LEVEL): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_DRY_LEVEL_TARGET): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_RAPID, default=0): vol.All(int, vol.Range(min=0, max=1)),
})

TD_STOP_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Optional(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
})

ENTRY_ONLY_SCHEMA = vol.Schema({
    vol.Required("entry_id"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Candy from a config entry."""

    ip_address = config_entry.data[CONF_IP_ADDRESS]
    encryption_key = config_entry.data.get(CONF_PASSWORD, "")
    use_encryption = config_entry.data.get(CONF_KEY_USE_ENCRYPTION, True)

    session = async_get_clientsession(hass)
    client = CandyClient(session, ip_address, encryption_key, use_encryption)

    async def update_status():
        try:
            async with async_timeout.timeout(40):
                status = await client.status_with_retry()
                _LOGGER.debug("Fetched status: %s", status)
                return status
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {repr(err)}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=60),
        update_method=update_status,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        DATA_KEY_COORDINATOR: coordinator,
        DATA_KEY_CLIENT: client,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    _async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            for service in (SERVICE_SEND_COMMAND, SERVICE_SEND_RAW_COMMAND,
                            SERVICE_SEND_PLAINTEXT_COMMAND, SERVICE_DECRYPT_DATA,
                            SERVICE_WM_START, SERVICE_WM_STOP,
                            SERVICE_WM_PAUSE, SERVICE_WM_RESUME,
                            SERVICE_TD_START, SERVICE_TD_STOP,
                            SERVICE_TD_PAUSE, SERVICE_TD_RESUME):
                hass.services.async_remove(DOMAIN, service)
            del hass.data[DOMAIN]

    return unload_ok


def _get_entry_data(hass: HomeAssistant, entry_id: str) -> dict:
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if entry_data is None:
        raise HomeAssistantError(f"No Candy config entry with id {entry_id}")
    return entry_data


def _get_client(hass: HomeAssistant, entry_id: str) -> CandyClient:
    return _get_entry_data(hass, entry_id)[DATA_KEY_CLIENT]


async def _send_plaintext(hass: HomeAssistant, entry_id: str, plaintext: str) -> None:
    client = _get_client(hass, entry_id)
    hex_blob = client.encrypt_command(plaintext)
    await client.send_encrypted_data(hex_blob)


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_RAW_COMMAND):
        return

    async def handle_send_command(call: ServiceCall) -> None:
        client = _get_client(hass, call.data["entry_id"])
        await client.send_command(call.data[ATTR_PARAMS])

    async def handle_send_raw_command(call: ServiceCall) -> None:
        client = _get_client(hass, call.data["entry_id"])
        await client.send_encrypted_data(call.data[ATTR_DATA])

    async def handle_send_plaintext_command(call: ServiceCall) -> None:
        client = _get_client(hass, call.data["entry_id"])
        hex_blob = client.encrypt_command(call.data[ATTR_PLAINTEXT])
        await client.send_encrypted_data(hex_blob)

    async def handle_decrypt_data(call: ServiceCall) -> None:
        client = _get_client(hass, call.data["entry_id"])
        plaintext = client.decrypt_data(call.data[ATTR_DATA])
        _LOGGER.warning("candy.decrypt_data result: %s", plaintext)

    async def handle_wm_start(call: ServiceCall) -> None:
        plaintext = washing_machine_start(
            program=call.data[ATTR_PROGRAM],
            temp=call.data.get(ATTR_TEMP),
            spin_target=call.data.get(ATTR_SPIN_TARGET),
            spin_default=call.data.get(ATTR_SPIN_DEFAULT),
            soil_level=call.data.get(ATTR_SOIL_LEVEL),
            steam=call.data.get(ATTR_STEAM, 0),
        )
        await _send_plaintext(hass, call.data["entry_id"], plaintext)

    async def handle_wm_stop(call: ServiceCall) -> None:
        program = call.data.get(ATTR_PROGRAM)
        if program is None:
            entry_data = _get_entry_data(hass, call.data["entry_id"])
            status = entry_data[DATA_KEY_COORDINATOR].data
            if not isinstance(status, WashingMachineStatus) or status.program is None:
                raise HomeAssistantError(
                    "Cannot determine current program — pass `program:` explicitly"
                )
            program = status.program
        await _send_plaintext(hass, call.data["entry_id"], washing_machine_stop(program))

    async def handle_wm_pause(call: ServiceCall) -> None:
        await _send_plaintext(hass, call.data["entry_id"], washing_machine_pause())

    async def handle_wm_resume(call: ServiceCall) -> None:
        await _send_plaintext(hass, call.data["entry_id"], washing_machine_resume())

    async def handle_td_start(call: ServiceCall) -> None:
        plaintext = tumble_dryer_start(
            program=call.data[ATTR_PROGRAM],
            dry_level=call.data.get(ATTR_DRY_LEVEL),
            dry_level_target=call.data.get(ATTR_DRY_LEVEL_TARGET),
            rapid=call.data.get(ATTR_RAPID, 0),
        )
        await _send_plaintext(hass, call.data["entry_id"], plaintext)

    async def handle_td_stop(call: ServiceCall) -> None:
        program = call.data.get(ATTR_PROGRAM)
        if program is None:
            entry_data = _get_entry_data(hass, call.data["entry_id"])
            status = entry_data[DATA_KEY_COORDINATOR].data
            if not isinstance(status, TumbleDryerStatus):
                raise HomeAssistantError(
                    "Cannot determine current program — pass `program:` explicitly"
                )
            program = status.program
        await _send_plaintext(hass, call.data["entry_id"], tumble_dryer_stop(program))

    async def handle_td_pause(call: ServiceCall) -> None:
        await _send_plaintext(hass, call.data["entry_id"], tumble_dryer_pause())

    async def handle_td_resume(call: ServiceCall) -> None:
        await _send_plaintext(hass, call.data["entry_id"], tumble_dryer_resume())

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_COMMAND, handle_send_command, schema=SEND_COMMAND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_RAW_COMMAND, handle_send_raw_command, schema=SEND_RAW_COMMAND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_PLAINTEXT_COMMAND, handle_send_plaintext_command, schema=SEND_PLAINTEXT_COMMAND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DECRYPT_DATA, handle_decrypt_data, schema=DECRYPT_DATA_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WM_START, handle_wm_start, schema=WM_START_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WM_STOP, handle_wm_stop, schema=WM_STOP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WM_PAUSE, handle_wm_pause, schema=ENTRY_ONLY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WM_RESUME, handle_wm_resume, schema=ENTRY_ONLY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TD_START, handle_td_start, schema=TD_START_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TD_STOP, handle_td_stop, schema=TD_STOP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TD_PAUSE, handle_td_pause, schema=ENTRY_ONLY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TD_RESUME, handle_td_resume, schema=ENTRY_ONLY_SCHEMA
    )
