"""Button entities for Candy machines: Pause / Resume / Stop."""
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
                              tumble_dryer_stop, washing_machine_pause,
                              washing_machine_resume, washing_machine_stop)
from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import *


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator = entry_data[DATA_KEY_COORDINATOR]
    client = entry_data[DATA_KEY_CLIENT]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashPauseButton(coordinator, client, config_id),
            CandyWashResumeButton(coordinator, client, config_id),
            CandyWashStopButton(coordinator, client, config_id),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumblePauseButton(coordinator, client, config_id),
            CandyTumbleResumeButton(coordinator, client, config_id),
            CandyTumbleStopButton(coordinator, client, config_id),
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


class CandyWashPauseButton(_WashBase):
    @property
    def name(self) -> str: return "Pause washing machine"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

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

    async def async_press(self) -> None:
        await _send(self._client, washing_machine_resume())


class CandyWashStopButton(_WashBase):
    @property
    def name(self) -> str: return "Stop washing machine"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_STOP_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:stop"

    async def async_press(self) -> None:
        status: WashingMachineStatus = self.coordinator.data
        if not isinstance(status, WashingMachineStatus) or status.program is None:
            raise HomeAssistantError(
                "Cannot stop: current program unknown — call washing_machine_stop service with explicit program"
            )
        await _send(self._client, washing_machine_stop(status.program))


class _TumbleBase(CandyBaseButton):
    def _device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def _suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM


class CandyTumblePauseButton(_TumbleBase):
    @property
    def name(self) -> str: return "Pause tumble dryer"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_PAUSE_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:pause"

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

    async def async_press(self) -> None:
        await _send(self._client, tumble_dryer_resume())


class CandyTumbleStopButton(_TumbleBase):
    @property
    def name(self) -> str: return "Stop tumble dryer"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_STOP_BUTTON.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:stop"

    async def async_press(self) -> None:
        status: TumbleDryerStatus = self.coordinator.data
        if not isinstance(status, TumbleDryerStatus) or status.program is None:
            raise HomeAssistantError(
                "Cannot stop: current program unknown — call tumble_dryer_stop service with explicit program"
            )
        await _send(self._client, tumble_dryer_stop(status.program))
