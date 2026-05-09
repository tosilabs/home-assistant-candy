"""Button entities for Candy machines: Start / Pause / Resume / Stop."""
from abc import abstractmethod

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .client import CandyClient
from .client.commands import (tumble_dryer_pause, tumble_dryer_resume,
                              tumble_dryer_start, tumble_dryer_stop,
                              washing_machine_pause, washing_machine_resume,
                              washing_machine_start, washing_machine_stop)
from .client.model import MachineState, TumbleDryerStatus, WashingMachineStatus
from .const import *
from .programs import (TUMBLE_DRYER_PROGRAMS_BY_NAME,
                       WASHING_MACHINE_PROGRAMS_BY_NAME)
from .select import UNIQUE_ID_TD_PROGRAM_SELECT, UNIQUE_ID_WM_PROGRAM_SELECT

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
    hex_blob = client.encrypt_command(plaintext)
    await client.send_encrypted_data(hex_blob)


class CandyBaseButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, client: CandyClient, config_id: str):
        super().__init__(coordinator)
        self._client = client
        self.config_id = config_id

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
    def __init__(self, coordinator, client, config_id, entry_data, hass):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data
        self._hass = hass

    @property
    def name(self) -> str: return "Start washing machine"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_START_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_IDLE

    async def async_press(self) -> None:
        from homeassistant.helpers import entity_registry as er
        select_uid = UNIQUE_ID_WM_PROGRAM_SELECT.format(self.config_id)
        registry = er.async_get(self._hass)
        entry = registry.async_get_entity_id("select", DOMAIN, select_uid)
        if entry is None:
            raise HomeAssistantError("Program select entity not found")
        state = self._hass.states.get(entry)
        if state is None:
            raise HomeAssistantError("Program select entity has no state")
        program_name = state.state
        prog = WASHING_MACHINE_PROGRAMS_BY_NAME.get(program_name)
        if prog is None:
            raise HomeAssistantError(f"Unknown program: {program_name}")
        # Apply user overrides from the number/select entities when set
        temp = self._entry_data.get(DATA_KEY_WM_TEMP, prog.temp)
        spin = self._entry_data.get(DATA_KEY_WM_SPIN, prog.spin_target)
        steam = self._entry_data.get(DATA_KEY_WM_STEAM, prog.steam)
        if steam is None:
            steam = prog.steam

        plaintext = washing_machine_start(
            program=prog.program,
            temp_target=temp,
            temp_default=prog.temp,
            spin_target=spin,
            spin_default=prog.spin_default,
            steam=steam,
            opt_mask=prog.opt_mask,
            selection=prog.position,  # pass cloud selector position (Sel) for downloadable programs
        )
        self._entry_data[DATA_KEY_LAST_PROGRAM] = prog.program
        await _send(self._client, plaintext)


class CandyWashPauseButton(_WashBase):
    @property
    def name(self) -> str: return "Pause washing machine"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_RUNNING

    async def async_press(self) -> None:
        await _send(self._client, washing_machine_pause())


class CandyWashResumeButton(_WashBase):
    @property
    def name(self) -> str: return "Resume washing machine"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_RESUME_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._wm_state() in _WM_PAUSED

    async def async_press(self) -> None:
        await _send(self._client, washing_machine_resume())


class CandyWashStopButton(_WashBase):
    def __init__(self, coordinator, client, config_id, entry_data):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data

    @property
    def name(self) -> str: return "Stop washing machine"

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
        await _send(self._client, washing_machine_stop(program))


class _TumbleBase(CandyBaseButton):
    def _device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def _suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM

    def _td_state(self):
        d = self.coordinator.data
        return d.machine_state if isinstance(d, TumbleDryerStatus) else None


class CandyTumbleStartButton(_TumbleBase):
    def __init__(self, coordinator, client, config_id, entry_data, hass):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data
        self._hass = hass

    @property
    def name(self) -> str: return "Start tumble dryer"

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
        program_name = state.state
        prog = TUMBLE_DRYER_PROGRAMS_BY_NAME.get(program_name)
        if prog is None:
            raise HomeAssistantError(f"Unknown program: {program_name}")
        dry_level = self._entry_data.get(DATA_KEY_TD_DRY_LEVEL, prog.dry_level)
        dry_time = self._entry_data.get(DATA_KEY_TD_TIME, prog.time)
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
        await _send(self._client, plaintext)


class CandyTumblePauseButton(_TumbleBase):
    @property
    def name(self) -> str: return "Pause tumble dryer"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_RUNNING

    async def async_press(self) -> None:
        await _send(self._client, tumble_dryer_pause())


class CandyTumbleResumeButton(_TumbleBase):
    @property
    def name(self) -> str: return "Resume tumble dryer"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_RESUME_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play"

    @property
    def available(self) -> bool:
        return super().available and self._td_state() in _WM_PAUSED

    async def async_press(self) -> None:
        await _send(self._client, tumble_dryer_resume())


class CandyTumbleStopButton(_TumbleBase):
    def __init__(self, coordinator, client, config_id, entry_data):
        super().__init__(coordinator, client, config_id)
        self._entry_data = entry_data

    @property
    def name(self) -> str: return "Stop tumble dryer"

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
        await _send(self._client, tumble_dryer_stop(program))
