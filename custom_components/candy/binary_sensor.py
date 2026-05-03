"""Binary sensor entities for Candy appliances."""
from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                     BinarySensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .client.model import TumbleDryerStatus
from .const import (DATA_KEY_COORDINATOR, DEVICE_NAME_TUMBLE_DRYER, DOMAIN,
                    SUGGESTED_AREA_BATHROOM, UNIQUE_ID_TD_DOOR,
                    UNIQUE_ID_TD_FILTER, UNIQUE_ID_TD_WATER_TANK)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]

    if isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumbleDoorSensor(coordinator, config_id),
            CandyTumbleFilterSensor(coordinator, config_id),
            CandyTumbleWaterTankSensor(coordinator, config_id),
        ])


class _TumbleBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, config_id: str):
        super().__init__(coordinator)
        self.config_id = config_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_TUMBLE_DRYER,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_BATHROOM,
        )


class CandyTumbleDoorSensor(_TumbleBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def name(self) -> str: return "Door"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_DOOR.format(self.config_id)

    @property
    def is_on(self) -> bool:
        return not self.coordinator.data.door_closed


class CandyTumbleFilterSensor(_TumbleBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def name(self) -> str: return "Clean filter"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_FILTER.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:air-filter"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.need_clean_filter


class CandyTumbleWaterTankSensor(_TumbleBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def name(self) -> str: return "Water tank full"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_WATER_TANK.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:water-alert"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.water_tank_full
