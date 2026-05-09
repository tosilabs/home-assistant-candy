"""Number entities for Candy washing machine and tumble dryer adjustable settings.

Improvements in this revision:
- Keep number entities in sync with last known API values on startup
- Ensure entry_data cache is always initialized so services can read it
- Minor naming cleanup for clarity in the HA UI
- Temperature validation: only accept Candy-supported values (0,20,30,40,60,90°C)
"""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import (
    DATA_KEY_COORDINATOR,
    DATA_KEY_TD_TIME,
    DATA_KEY_WM_SPIN,
    DATA_KEY_WM_TEMP,
    DEVICE_NAME_TUMBLE_DRYER,
    DEVICE_NAME_WASHING_MACHINE,
    DOMAIN,
    SIGNAL_WM_PROGRAM_CHANGED,
    SUGGESTED_AREA_KITCHEN,
    SUGGESTED_AREA_BATHROOM,
    UNIQUE_ID_TD_TIME_NUMBER,
    UNIQUE_ID_WM_SPIN,
    UNIQUE_ID_WM_TEMP,
)

# Valid Candy wash temperatures in °C. Values outside this set are rejected.
_VALID_WASH_TEMPS = (0, 20, 30, 40, 60, 90)


def _nearest_valid_temp(value: float) -> float:
    """Snap a temperature value to the nearest valid Candy wash temperature."""
    return float(min(_VALID_WASH_TEMPS, key=lambda t: abs(t - value)))


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up Candy number entities for a config entry."""
    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator = entry_data[DATA_KEY_COORDINATOR]

    # Ensure the shared dict has defaults so services can safely read values
    entry_data.setdefault(DATA_KEY_WM_TEMP, None)
    entry_data.setdefault(DATA_KEY_WM_SPIN, None)
    entry_data.setdefault(DATA_KEY_TD_TIME, None)

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities(
            [
                CandyWashTemperatureNumber(config_id, entry_data),
                CandyWashSpinSpeedNumber(config_id, entry_data),
            ]
        )
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([CandyTumbleTimeNumber(config_id, entry_data)])


class _WashNumberBase(RestoreEntity, NumberEntity):
    """Base class for washing machine number entities."""

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_WASHING_MACHINE,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_KITCHEN,
        )


class CandyWashTemperatureNumber(_WashNumberBase):
    """Configured target wash temperature.

    This is the value sent when starting a new program, not a live sensor.
    Only values supported by Candy appliances are accepted: 0, 20, 30, 40, 60, 90 °C.
    Any value outside this set is snapped to the nearest valid temperature and a
    warning is logged.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 90
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "°C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_id: str, entry_data: dict):
        super().__init__(config_id, entry_data)
        self._value = 40.0

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_TEMP.format(self.config_id)

    @property
    def name(self) -> str:
        return "02 Temperature"

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        snapped = _nearest_valid_temp(value)
        if snapped != value:
            import logging
            logging.getLogger(__name__).warning(
                "Candy wash temperature %s°C is not a valid Candy value; "
                "snapping to nearest valid temperature %s°C. "
                "Valid values: %s",
                value, snapped, _VALID_WASH_TEMPS,
            )
        self._value = snapped
        self._entry_data[DATA_KEY_WM_TEMP] = int(snapped)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable"):
            try:
                raw = float(last.state)
                self._value = _nearest_valid_temp(raw)
                self._entry_data[DATA_KEY_WM_TEMP] = int(self._value)
            except ValueError:
                pass

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                self._on_program_changed,
            )
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        if prog.temp is not None:
            self._value = _nearest_valid_temp(float(prog.temp))
            self._entry_data[DATA_KEY_WM_TEMP] = int(self._value)
            self.async_write_ha_state()


class CandyWashSpinSpeedNumber(_WashNumberBase):
    """Configured target spin speed.

    Value is stored as rpm for the UI but converted back to the internal
    API representation (hundreds of rpm) in the shared entry data.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:rotate-right"
    _attr_native_min_value = 0
    _attr_native_max_value = 1500
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "rpm"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_id: str, entry_data: dict):
        super().__init__(config_id, entry_data)
        self._value = 1000.0

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_SPIN.format(self.config_id)

    @property
    def name(self) -> str:
        return "05 Spin speed"

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self._entry_data[DATA_KEY_WM_SPIN] = int(value) // 100
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable"):
            try:
                self._value = float(last.state)
                self._entry_data[DATA_KEY_WM_SPIN] = int(self._value) // 100
            except ValueError:
                pass

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                self._on_program_changed,
            )
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        if prog.spin_target is not None:
            self._value = float(prog.spin_target * 100)
            self._entry_data[DATA_KEY_WM_SPIN] = prog.spin_target
            self.async_write_ha_state()


class CandyTumbleTimeNumber(RestoreEntity, NumberEntity):
    """Drying time selection for time-based tumble dryer programs."""

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
        return "Drying in time"

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
