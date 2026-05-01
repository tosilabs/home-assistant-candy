from abc import abstractmethod
from typing import Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .client import (CandyClient, DishwasherStatus, OvenStatus,
                     TumbleDryerStatus, WashingMachineStatus)
from .client.commands import pause_payload, resume_payload
from .const import *


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the Candy buttons from config entry."""

    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator: DataUpdateCoordinator = entry_data[DATA_KEY_COORDINATOR]
    client: CandyClient = entry_data[DATA_KEY_CLIENT]

    if isinstance(coordinator.data, WashingMachineStatus):
        device_name = DEVICE_NAME_WASHING_MACHINE
        suggested_area = SUGGESTED_AREA_BATHROOM
        pause_uid = UNIQUE_ID_WASH_PAUSE_BUTTON
        resume_uid = UNIQUE_ID_WASH_RESUME_BUTTON
    elif isinstance(coordinator.data, TumbleDryerStatus):
        device_name = DEVICE_NAME_TUMBLE_DRYER
        suggested_area = SUGGESTED_AREA_BATHROOM
        pause_uid = UNIQUE_ID_TUMBLE_PAUSE_BUTTON
        resume_uid = UNIQUE_ID_TUMBLE_RESUME_BUTTON
    elif isinstance(coordinator.data, OvenStatus):
        device_name = DEVICE_NAME_OVEN
        suggested_area = SUGGESTED_AREA_KITCHEN
        pause_uid = UNIQUE_ID_OVEN_PAUSE_BUTTON
        resume_uid = UNIQUE_ID_OVEN_RESUME_BUTTON
    elif isinstance(coordinator.data, DishwasherStatus):
        device_name = DEVICE_NAME_DISHWASHER
        suggested_area = SUGGESTED_AREA_KITCHEN
        pause_uid = UNIQUE_ID_DISHWASHER_PAUSE_BUTTON
        resume_uid = UNIQUE_ID_DISHWASHER_RESUME_BUTTON
    else:
        raise Exception(f"Unable to determine machine type: {coordinator.data}")

    async_add_entities([
        CandyPauseButton(coordinator, client, config_id, device_name, suggested_area, pause_uid),
        CandyResumeButton(coordinator, client, config_id, device_name, suggested_area, resume_uid),
    ])


class CandyCommandButton(CoordinatorEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: CandyClient,
        config_id: str,
        device_name: str,
        suggested_area: str,
        unique_id: str,
    ):
        super().__init__(coordinator)
        self._client = client
        self._config_id = config_id
        self._device_name = device_name
        self._suggested_area = suggested_area
        self._unique_id = unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_id)},
            name=self._device_name,
            manufacturer="Candy",
            suggested_area=self._suggested_area,
        )

    @property
    def unique_id(self) -> str:
        return self._unique_id.format(self._config_id)

    @property
    def icon(self) -> Optional[str]:
        return None

    @abstractmethod
    async def async_press(self) -> None:
        ...


class CandyPauseButton(CandyCommandButton):
    @property
    def name(self) -> str:
        return "Pause"

    @property
    def icon(self) -> str:
        return "mdi:pause"

    async def async_press(self) -> None:
        await self._client.send_command(pause_payload())


class CandyResumeButton(CandyCommandButton):
    @property
    def name(self) -> str:
        return "Resume"

    @property
    def icon(self) -> str:
        return "mdi:play"

    async def async_press(self) -> None:
        await self._client.send_command(resume_payload())
