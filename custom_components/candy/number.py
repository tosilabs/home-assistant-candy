"""Number entities for Candy washing machine adjustable settings."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import WashingMachineStatus
from .const import (DATA_KEY_COORDINATOR, DATA_KEY_WM_SPIN, DATA_KEY_WM_TEMP,
                    DEVICE_NAME_WASHING_MACHINE, DOMAIN,
                    SIGNAL_WM_PROGRAM_CHANGED, SUGGESTED_AREA_KITCHEN,
                    UNIQUE_ID_WM_SPIN, UNIQUE_ID_WM_TEMP)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][config_id]
    coordinator = entry_data[DATA_KEY_COORDINATOR]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashTemperatureNumber(config_id, entry_data),
            CandyWashSpinSpeedNumber(config_id, entry_data),
        ])


class _WashNumberBase(RestoreEntity, NumberEntity):
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
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 90
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "°C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_id, entry_data):
        super().__init__(config_id, entry_data)
        self._value = 40.0

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_TEMP.format(self.config_id)

    @property
    def name(self) -> str:
        return "Temperature"

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self._entry_data[DATA_KEY_WM_TEMP] = int(value)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable"):
            try:
                self._value = float(last.state)
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
            self._value = float(prog.temp)
            self._entry_data[DATA_KEY_WM_TEMP] = prog.temp
            self.async_write_ha_state()


class CandyWashSpinSpeedNumber(_WashNumberBase):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:rotate-right"
    _attr_native_min_value = 0
    _attr_native_max_value = 1500
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "rpm"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_id, entry_data):
        super().__init__(config_id, entry_data)
        self._value = 1000.0

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_SPIN.format(self.config_id)

    @property
    def name(self) -> str:
        return "Spin speed"

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
