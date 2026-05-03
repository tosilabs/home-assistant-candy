"""The Candy integration."""
from __future__ import annotations

import logging
import re
from datetime import timedelta

import async_timeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
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


def _target_required(schema: dict) -> vol.Schema:
    """Schema where the call must include either device_id (HA target) or entry_id."""
    base = {
        vol.Optional("entry_id"): cv.string,
        vol.Optional("device_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("area_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("entity_id"): vol.All(cv.ensure_list, [cv.string]),
    }
    base.update(schema)
    return vol.All(
        vol.Schema(base, extra=vol.ALLOW_EXTRA),
        _require_target,
    )


def _require_target(value: dict) -> dict:
    if not value.get("entry_id") and not value.get("device_id"):
        raise vol.Invalid("Either `device_id` (target) or `entry_id` must be provided")
    return value


SEND_COMMAND_SCHEMA = _target_required({
    vol.Required(ATTR_PARAMS): vol.Schema({cv.string: vol.Any(cv.string, int)}),
})

SEND_RAW_COMMAND_SCHEMA = _target_required({
    vol.Required(ATTR_DATA): _hex_string,
})

SEND_PLAINTEXT_COMMAND_SCHEMA = _target_required({
    vol.Required(ATTR_PLAINTEXT): cv.string,
})

DECRYPT_DATA_SCHEMA = _target_required({
    vol.Required(ATTR_DATA): _hex_string,
})

WM_START_SCHEMA = _target_required({
    vol.Required(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_TEMP): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SPIN_TARGET): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SPIN_DEFAULT): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_SOIL_LEVEL): vol.All(int, vol.Range(min=0)),
    vol.Optional(ATTR_STEAM, default=0): vol.All(int, vol.Range(min=0, max=1)),
})

WM_STOP_SCHEMA = _target_required({
    vol.Optional(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
})

TD_START_SCHEMA = _target_required({
    vol.Required(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
})

TD_STOP_SCHEMA = _target_required({
    vol.Optional(ATTR_PROGRAM): vol.All(int, vol.Range(min=0)),
})

ENTRY_ONLY_SCHEMA = _target_required({})


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

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        DATA_KEY_COORDINATOR: coordinator,
        DATA_KEY_CLIENT: client,
        DATA_KEY_LAST_PROGRAM: None,
        DATA_KEY_PLATFORMS_LOADED: False,
        DATA_KEY_SETUP_RETRY_UNSUB: None,
    }

    _async_register_services(hass)

    async def _try_load_platforms() -> None:
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
        if entry_data[DATA_KEY_PLATFORMS_LOADED] or coordinator.data is None:
            return
        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
        entry_data[DATA_KEY_PLATFORMS_LOADED] = True
        unsub = entry_data.get(DATA_KEY_SETUP_RETRY_UNSUB)
        if unsub:
            unsub()
            entry_data[DATA_KEY_SETUP_RETRY_UNSUB] = None

    await coordinator.async_refresh()
    if coordinator.last_update_success and coordinator.data is not None:
        await _try_load_platforms()
    else:
        _LOGGER.warning(
            "Initial Candy status fetch failed (device may be off/unreachable). "
            "Will keep retrying in background without failing setup."
        )

        @callback
        def _retry_setup(_now) -> None:
            async def _do_retry() -> None:
                await coordinator.async_refresh()
                if coordinator.last_update_success and coordinator.data is not None:
                    await _try_load_platforms()
            hass.async_create_task(_do_retry())

        hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_SETUP_RETRY_UNSUB] = async_track_time_interval(
            hass, _retry_setup, timedelta(seconds=60)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].get(entry.entry_id)
        if entry_data:
            unsub = entry_data.get(DATA_KEY_SETUP_RETRY_UNSUB)
            if unsub:
                unsub()
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


def _resolve_entry_id(hass: HomeAssistant, call: ServiceCall) -> str:
    """Resolve the Candy config entry id from a service call.

    Accepts either:
      - explicit `entry_id` (legacy), or
      - HA target `device_id` (preferred — populated by the device selector)

    If multiple device_ids are passed, the first one that maps to a Candy entry wins.
    """
    explicit = call.data.get("entry_id")
    if explicit:
        return explicit

    device_ids = call.data.get("device_id") or []
    if device_ids:
        registry = dr.async_get(hass)
        for device_id in device_ids:
            device = registry.async_get(device_id)
            if device is None:
                continue
            for entry_id in device.config_entries:
                if entry_id in hass.data.get(DOMAIN, {}):
                    return entry_id

    raise HomeAssistantError(
        "No Candy device targeted. Pass `device_id` (via the device selector) "
        "or `entry_id` explicitly."
    )


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
        client = _get_client(hass, _resolve_entry_id(hass, call))
        await client.send_command(call.data[ATTR_PARAMS])

    async def handle_send_raw_command(call: ServiceCall) -> None:
        client = _get_client(hass, _resolve_entry_id(hass, call))
        await client.send_encrypted_data(call.data[ATTR_DATA])

    async def handle_send_plaintext_command(call: ServiceCall) -> None:
        client = _get_client(hass, _resolve_entry_id(hass, call))
        hex_blob = client.encrypt_command(call.data[ATTR_PLAINTEXT])
        await client.send_encrypted_data(hex_blob)

    async def handle_decrypt_data(call: ServiceCall) -> None:
        client = _get_client(hass, _resolve_entry_id(hass, call))
        plaintext = client.decrypt_data(call.data[ATTR_DATA])
        _LOGGER.warning("candy.decrypt_data result: %s", plaintext)

    async def handle_wm_start(call: ServiceCall) -> None:
        program = call.data[ATTR_PROGRAM]
        plaintext = washing_machine_start(
            program=program,
            temp=call.data.get(ATTR_TEMP),
            spin_target=call.data.get(ATTR_SPIN_TARGET),
            spin_default=call.data.get(ATTR_SPIN_DEFAULT),
            soil_level=call.data.get(ATTR_SOIL_LEVEL),
            steam=call.data.get(ATTR_STEAM, 0),
        )
        entry_id = _resolve_entry_id(hass, call)
        _get_entry_data(hass, entry_id)[DATA_KEY_LAST_PROGRAM] = program
        await _send_plaintext(hass, entry_id, plaintext)

    async def handle_wm_stop(call: ServiceCall) -> None:
        program = call.data.get(ATTR_PROGRAM)
        entry_id = _resolve_entry_id(hass, call)
        entry_data = _get_entry_data(hass, entry_id)
        if program is None:
            status = entry_data[DATA_KEY_COORDINATOR].data
            if isinstance(status, WashingMachineStatus) and status.program is not None:
                program = status.program
            else:
                program = entry_data.get(DATA_KEY_LAST_PROGRAM)
            if program is None:
                raise HomeAssistantError(
                    "Cannot determine current program — pass `program:` explicitly"
                )
        await _send_plaintext(hass, entry_id, washing_machine_stop(program))

    async def handle_wm_pause(call: ServiceCall) -> None:
        await _send_plaintext(hass, _resolve_entry_id(hass, call), washing_machine_pause())

    async def handle_wm_resume(call: ServiceCall) -> None:
        await _send_plaintext(hass, _resolve_entry_id(hass, call), washing_machine_resume())

    async def handle_td_start(call: ServiceCall) -> None:
        program = call.data[ATTR_PROGRAM]
        plaintext = tumble_dryer_start(program=program)
        entry_id = _resolve_entry_id(hass, call)
        _get_entry_data(hass, entry_id)[DATA_KEY_LAST_PROGRAM] = program
        await _send_plaintext(hass, entry_id, plaintext)

    async def handle_td_stop(call: ServiceCall) -> None:
        program = call.data.get(ATTR_PROGRAM)
        entry_id = _resolve_entry_id(hass, call)
        entry_data = _get_entry_data(hass, entry_id)
        if program is None:
            status = entry_data[DATA_KEY_COORDINATOR].data
            if isinstance(status, TumbleDryerStatus) and status.program is not None:
                program = status.program
            else:
                program = entry_data.get(DATA_KEY_LAST_PROGRAM)
            if program is None:
                raise HomeAssistantError(
                    "Cannot determine current program — pass `program:` explicitly"
                )
        await _send_plaintext(hass, entry_id, tumble_dryer_stop(program))

    async def handle_td_pause(call: ServiceCall) -> None:
        await _send_plaintext(hass, _resolve_entry_id(hass, call), tumble_dryer_pause())

    async def handle_td_resume(call: ServiceCall) -> None:
        await _send_plaintext(hass, _resolve_entry_id(hass, call), tumble_dryer_resume())

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
