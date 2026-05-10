"""Number entities for Candy machines — tumble dryer drying time only.

NOTE: WM Temperature and Spin Speed are now handled by select entities
(CandyWashTemperatureSelect / CandyWashSpinSelect in select.py) which
provide discrete options constrained by the selected program.
The old UNIQUE_ID_WM_TEMP / UNIQUE_ID_WM_SPIN constants are kept in
const.py for migration purposes but no longer create entities here.
"""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import (
    DATA_KEY_COORDINATOR,
    DATA_KEY_TD_TIME,
    DEVICE_NAME_TUMBLE_DRYER,
    DOMAIN,
    SUGGESTED_AREA_BATHROOM,
    UNIQUE_ID_TD_TIME_NUMBER,
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator = entry_data[DATA_KEY_COORDINATOR]

    entry_data.setdefault(DATA_KEY_TD_TIME, None)

    # WM Temperature + Spin are now select entities in select.py
    if isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([CandyTumbleTimeNumber(config_id, entry_data)])


class CandyTumbleTimeNumber(RestoreEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 30
    _attr_native_max_value = 220
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._value = 90.0

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_TIME_NUMBER.format(self.config_id)

    @property
    def name(self) -> str:
        return "Drying time"

    @property
    def native_value(self) -> float:
        return self._value

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_TUMBLE_DRYER,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_BATHROOM,
        )

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self._entry_data[DATA_KEY_TD_TIME] = int(value)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable"):
            try:
                self._value = float(last.state)
                self._entry_data[DATA_KEY_TD_TIME] = int(self._value)
            except ValueError:
                pass
