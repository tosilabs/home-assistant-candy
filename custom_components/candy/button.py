"""Button entities for Candy machines: Start / Pause / Resume / Stop."""
from abc import abstractmethod
import asyncio
from datetime import datetime, timezone
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .program_options import resolve_dry_name
from .start_status import start_outcome, status_snapshot
from .wash_settings import PROGRAM_NAME, wash_command_parameters, select_wash_program
from .client import CandyClient
from .client.commands import (tumble_dryer_pause, tumble_dryer_resume,
                              tumble_dryer_start, tumble_dryer_stop,
                              washing_machine_pause, washing_machine_resume,
                              washing_machine_start, washing_machine_stop)
from .client.model import MachineState, TumbleDryerStatus, WashingMachineStatus, WashProgramState
from .const import *
from .programs import (TUMBLE_DRYER_PROGRAMS_BY_NAME,
                       WASHING_MACHINE_PROGRAMS_BY_NAME)
from .select import UNIQUE_ID_TD_PROGRAM_SELECT, UNIQUE_ID_WM_PROGRAM_SELECT

_LOGGER = logging.getLogger(__name__)


class StartNotConfirmed(HomeAssistantError):
    """A Start request did not produce a fresh running/scheduled status."""


_WM_IDLE = (MachineState.IDLE, MachineState.FINISHED1, MachineState.FINISHED2)
_WM_RUNNING = (MachineState.RUNNING,)
_WM_PAUSED = (MachineState.PAUSED,)
_WM_STOPPABLE = (
    MachineState.RUNNING, MachineState.PAUSED,
    MachineState.DELAYED_START_SELECTION, MachineState.DELAYED_START_PROGRAMMED,
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator = entry_data[DATA_KEY_COORDINATOR]
    client = entry_data[DATA_KEY_CLIENT]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashStartButton(coordinator, client, config_id, entry_data, hass),
            CandyWashPrepareButton(coordinator, client, config_id, entry_data),
            CandyWashPauseButton(coordinator, client, config_id),
            CandyWashResumeButton(coordinator, client, config_id),
            CandyWashStopButton(coordinator, client, config_id, entry_data),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumbleStartButton(coordinator, client, config_id, entry_data, hass),
            CandyTumblePauseButton(coordinator, client, config_id),
            CandyTumbleResumeButton(coordinator, client, config_id),
            CandyTumbleStopButton(coordinator, client, config_id, entry_data),
        ])


async def _send(client: CandyClient, plaintext: str) -> None:
    await client.send_plaintext(plaintext)


class CandyBaseButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator: DataUpdateCoordinator, client: CandyClient, config_id: str):
        super().__init__(coordinator)
        self._client = client
        self.config_id = config_id

    @property
    def available(self) -> bool:
        return (
            super().available
            and bool(getattr(self.coordinator.data, "remote_control", False))
            and not self._client.write_pending
        )

    async def _send_and_refresh(self, plaintext: str, *, verify_start=False) -> str | None:
        if not self.available:
            raise HomeAssistantError("Machine is busy, offline, or remote control is disabled")
        self._client.write_pending = True
        self.coordinator.async_update_listeners()
        try:
            await _send(self._client, plaintext)
            # A successful HTTP response can still be an ignored Start request.
            # Poll status only: never resend Start automatically.
            await asyncio.sleep(5)
            await self.coordinator.async_request_refresh()
            if verify_start:
                for attempt in range(3):
                    outcome = start_outcome(
                        self.coordinator.data, self.coordinator.last_update_success
                    )
                    if outcome in ("running_recipe_unverified", "scheduled_recipe_unverified"):
                        return outcome
                    if outcome == "device_error":
                        raise StartNotConfirmed("The machine reports an error after Start. Check its panel.")
                    if attempt < 2:
                        await asyncio.sleep(3)
                        await self.coordinator.async_request_refresh()
                raise StartNotConfirmed(
                    "Start was sent, but the machine did not confirm a running or scheduled cycle. "
                    "Check Remote control and the physical panel. Download Candy diagnostics "
                    "from the integration menu to inspect the requested command and reported status."
                )
            return None
        finally:
            self._client.write_pending = False
            self.coordinator.async_update_listeners()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=self._device_name(),
            manufacturer="Candy",
            suggested_area=self._suggested_area(),
        )

    @abstractmethod
    def _device_name(self) -> str: ...

    @abstractmethod
    def _suggested_area(self) -> str: ...


class _WashBase(CandyBaseButton):
    def _device_name(self) -> str:
        return DEVICE_NAME_WASHING_MACHINE

    def _suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    def _wm_state(self):
        d = self.coordinator.data
        return d.machine_state if isinstance(d, WashingMachineStatus) else None


class CandyWashStartButton(_WashBase):
    _attr_translation_key = "wash_start_button"
    def __init__(self, coordinator, client, config_id, entry_data, hass):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data
        self._hass = hass

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_START_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return (
            super().available and self._wm_state() in _WM_IDLE
            and self._entry_data.get("last_prepare", {}).get("result")
            not in ("preparing", "not_confirmed", "failed")
        )

    async def async_press(self) -> None:
        program_name = self._entry_data.get(PROGRAM_NAME)
        prog = WASHING_MACHINE_PROGRAMS_BY_NAME.get(program_name)
        if prog is None:
            raise HomeAssistantError("Select a wash program before starting")
        if not self.available:
            raise HomeAssistantError("Start unavailable: enable remote control and check the machine state")
        params = wash_command_parameters(self._entry_data)
        plaintext = washing_machine_start(**params)
        diagnostic = {
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "program_name": prog.name,
            "command_parameters": params,
            "plaintext_command": plaintext,
            "before": status_snapshot(self.coordinator.data),
            "result": "sending",
            "recipe_confirmed": False,
        }
        self._entry_data["last_start"] = diagnostic
        self.coordinator.async_update_listeners()
        try:
            diagnostic["result"] = await self._send_and_refresh(plaintext, verify_start=True)
        except StartNotConfirmed:
            diagnostic["result"] = start_outcome(
                self.coordinator.data, self.coordinator.last_update_success
            )
            _LOGGER.warning(
                "Candy Start not confirmed for %s: requested %s C / %s rpm; reported %s",
                prog.name, params["temp_target"],
                params["spin_target"] * 100 if params["spin_target"] is not None else None,
                status_snapshot(self.coordinator.data),
            )
            raise
        except Exception:
            diagnostic["result"] = "send_failed"
            raise
        else:
            self._entry_data[DATA_KEY_LAST_PROGRAM] = prog.effective_stop_program
            self._entry_data["last_requested_program"] = prog.name
        finally:
            diagnostic["after"] = status_snapshot(self.coordinator.data)
            self.coordinator.async_update_listeners()


class CandyWashPauseButton(_WashBase):
    _attr_translation_key = "wash_pause_button"
    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_RUNNING

    async def async_press(self) -> None:
        await self._send_and_refresh(washing_machine_pause())


class CandyWashResumeButton(_WashBase):
    _attr_translation_key = "wash_resume_button"
    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_RESUME_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_PAUSED

    async def async_press(self) -> None:
        await self._send_and_refresh(washing_machine_resume())


class CandyWashStopButton(_WashBase):
    _attr_translation_key = "wash_stop_button"
    def __init__(self, coordinator, client, config_id, entry_data):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_STOP_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:stop"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_STOPPABLE

    async def async_press(self) -> None:
        status = self.coordinator.data
        program = None
        if isinstance(status, WashingMachineStatus) and status.program is not None:
            program = status.program
        else:
            program = self._entry_data.get(DATA_KEY_LAST_PROGRAM)
        if program is None:
            raise HomeAssistantError(
                "Cannot stop: program unknown. Start a program from HA first, or call "
                "washing_machine_stop service with explicit program."
            )
        await self._send_and_refresh(washing_machine_stop(program))


class _TumbleBase(CandyBaseButton):
    def _device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def _suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM

    def _td_state(self):
        d = self.coordinator.data
        return d.machine_state if isinstance(d, TumbleDryerStatus) else None


class CandyTumbleStartButton(_TumbleBase):
    _attr_translation_key = "tumble_start_button"
    def __init__(self, coordinator, client, config_id, entry_data, hass):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data
        self._hass = hass

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_START_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_IDLE

    async def async_press(self) -> None:
        from homeassistant.helpers import entity_registry as er
        select_uid = UNIQUE_ID_TD_PROGRAM_SELECT.format(self.config_id)
        registry = er.async_get(self._hass)
        entry = registry.async_get_entity_id("select", DOMAIN, select_uid)
        if entry is None:
            raise HomeAssistantError("Tumble program select entity not found")
        state = self._hass.states.get(entry)
        if state is None:
            raise HomeAssistantError("Tumble program select entity has no state")
        program_name = resolve_dry_name(state.state)
        prog = TUMBLE_DRYER_PROGRAMS_BY_NAME.get(program_name)
        if prog is None:
            raise HomeAssistantError(f"Unknown program: {program_name}")
        dry_level = self._entry_data.get(DATA_KEY_TD_DRY_LEVEL, prog.dry_level)
        dry_time = self._entry_data.get(DATA_KEY_TD_TIME, prog.time)
        if dry_level is None:
            dry_level = prog.dry_level
        if dry_time is None:
            dry_time = prog.time
        plaintext = tumble_dryer_start(
            program=prog.program,
            time=dry_time,
            opt_mask=prog.opt_mask,
            dry_level=dry_level,
            selection=prog.selection,
            rapid=prog.rapid,
            pr_str=prog.name,
        )
        self._entry_data[DATA_KEY_LAST_PROGRAM] = prog.program
        await self._send_and_refresh(plaintext)


class CandyTumblePauseButton(_TumbleBase):
    _attr_translation_key = "tumble_pause_button"
    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_RUNNING

    async def async_press(self) -> None:
        await self._send_and_refresh(tumble_dryer_pause())


class CandyTumbleResumeButton(_TumbleBase):
    _attr_translation_key = "tumble_resume_button"
    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_RESUME_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_PAUSED

    async def async_press(self) -> None:
        await self._send_and_refresh(tumble_dryer_resume())


class CandyTumbleStopButton(_TumbleBase):
    _attr_translation_key = "tumble_stop_button"
    def __init__(self, coordinator, client, config_id, entry_data):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_STOP_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:stop"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_STOPPABLE

    async def async_press(self) -> None:
        status = self.coordinator.data
        program = None
        if isinstance(status, TumbleDryerStatus) and status.program is not None:
            program = status.program
        else:
            program = self._entry_data.get(DATA_KEY_LAST_PROGRAM)
        if program is None:
            raise HomeAssistantError(
                "Cannot stop: program unknown. Start a program from HA first, or call "
                "tumble_dryer_stop service with explicit program."
            )
        await self._send_and_refresh(tumble_dryer_stop(program))


class CandyWashPrepareButton(_WashBase):
    """Explicitly cancel a previous cycle; never start a new one automatically."""
    _attr_translation_key = "wash_prepare_button"
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator, client, config_id, entry_data):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data

    @property
    def unique_id(self):
        return f"{self.config_id}-wash_prepare_button"

    @property
    def available(self):
        return (
            super().available
            and self._wm_state() in (*_WM_IDLE, *_WM_STOPPABLE)
            and self._entry_data.get(PROGRAM_NAME) in WASHING_MACHINE_PROGRAMS_BY_NAME
        )

    async def async_press(self):
        if not self.available:
            raise HomeAssistantError("Enable remote control and select a program before preparing a new wash")
        program_name = self._entry_data[PROGRAM_NAME]
        record = {"requested_at": datetime.now(timezone.utc).isoformat(),
                  "selected_program": program_name, "result": "preparing",
                  "stop_sent": False}
        self._entry_data["last_prepare"] = record
        self._client.write_pending = True
        self.coordinator.async_update_listeners()
        try:
            # Resolve the current device program from a fresh read, never from
            # the next selected recipe or a remembered previous Start.
            await self.coordinator.async_request_refresh()
            status = self.coordinator.data
            if not self.coordinator.last_update_success or not isinstance(status, WashingMachineStatus):
                raise HomeAssistantError("Cannot prepare: fresh machine status is unavailable")
            record["before"] = status_snapshot(status)
            if not status.remote_control or status.machine_state not in (*_WM_IDLE, *_WM_STOPPABLE):
                raise HomeAssistantError("Cannot prepare: the machine does not currently allow this operation")
            current_program = status.program
            if current_program is None or current_program <= 0:
                if status.machine_state != MachineState.IDLE or status.program_state != WashProgramState.STOPPED:
                    raise HomeAssistantError("Cannot cancel: the machine's current program number is unknown")
                # Already Ready and no current program: only reset local recipe settings.
            else:
                command = washing_machine_stop(current_program)
                record["stop_command"] = command
                await _send(self._client, command)
                record["stop_sent"] = True
                for attempt in range(3):
                    await asyncio.sleep(5 if attempt == 0 else 3)
                    await self.coordinator.async_request_refresh()
                    status = self.coordinator.data
                    if (self.coordinator.last_update_success
                            and isinstance(status, WashingMachineStatus)
                            and status.machine_state == MachineState.IDLE
                            and status.program_state == WashProgramState.STOPPED):
                        break
                else:
                    record["result"] = "not_confirmed"
                    raise HomeAssistantError("Cancellation was not confirmed. No new wash was started; check the machine panel")
            select_wash_program(self._entry_data, program_name)
            async_dispatcher_send(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                  WASHING_MACHINE_PROGRAMS_BY_NAME[program_name])
            self._entry_data[DATA_KEY_LAST_PROGRAM] = None
            record["result"] = "ready"
        except Exception:
            if record["result"] == "preparing":
                record["result"] = "failed"
            raise
        finally:
            record["after"] = status_snapshot(self.coordinator.data)
            self._client.write_pending = False
            self.coordinator.async_update_listeners()
