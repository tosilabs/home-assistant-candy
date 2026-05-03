"""Select entities for Candy program selection and wash settings."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import (DATA_KEY_COORDINATOR, DATA_KEY_WM_SOIL, DATA_KEY_WM_STEAM,
                    DEVICE_NAME_TUMBLE_DRYER, DEVICE_NAME_WASHING_MACHINE, DOMAIN,
                    SIGNAL_WM_PROGRAM_CHANGED, SUGGESTED_AREA_BATHROOM,
                    SUGGESTED_AREA_KITCHEN, UNIQUE_ID_WM_SOIL, UNIQUE_ID_WM_STEAM)
from .programs import (TUMBLE_DRYER_PROGRAMS, WASHING_MACHINE_PROGRAMS,
                       WASHING_MACHINE_PROGRAMS_BY_NAME)

UNIQUE_ID_WM_PROGRAM_SELECT = "{0}-wm_program_select"
UNIQUE_ID_TD_PROGRAM_SELECT = "{0}-td_program_select"

_SOIL_OPTIONS = ["None", "Light", "Medium", "Heavy"]
_SOIL_TO_VALUE = {"None": None, "Light": 1, "Medium": 2, "Heavy": 3}
_SOIL_FROM_VALUE = {None: "None", 0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}

_STEAM_OPTIONS = ["Off", "Low", "High"]
_STEAM_TO_VALUE = {"Off": 0, "Low": 1, "High": 2}
_STEAM_FROM_VALUE = {0: "Off", 1: "Low", 2: "High"}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]
    entry_data = hass.data[DOMAIN][config_id]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashProgramSelect(config_id),
            CandyWashSoilLevelSelect(config_id, entry_data),
            CandyWashSteamSelect(config_id, entry_data),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([CandyTumbleProgramSelect(config_id)])


class CandyWashProgramSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str):
        self.config_id = config_id
        self._current_option = WASHING_MACHINE_PROGRAMS[0].name

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_PROGRAM_SELECT.format(self.config_id)

    @property
    def name(self) -> str:
        return "01 Program"

    @property
    def options(self) -> list[str]:
        return sorted((p.name for p in WASHING_MACHINE_PROGRAMS), key=str.casefold)

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def icon(self) -> str:
        return "mdi:washing-machine"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_WASHING_MACHINE,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_KITCHEN,
        )

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        prog = WASHING_MACHINE_PROGRAMS_BY_NAME.get(option)
        if prog:
            from homeassistant.helpers.dispatcher import async_dispatcher_send
            async_dispatcher_send(
                self.hass,
                SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                prog,
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self.options:
            self._current_option = last_state.state


class CandyWashSoilLevelSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._current = "Medium"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_SOIL.format(self.config_id)

    @property
    def name(self) -> str:
        return "03 Soil level"

    @property
    def options(self) -> list[str]:
        return _SOIL_OPTIONS

    @property
    def current_option(self) -> str:
        return self._current

    @property
    def icon(self) -> str:
        return "mdi:water-opacity"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_WASHING_MACHINE,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_KITCHEN,
        )

    async def async_select_option(self, option: str) -> None:
        if option not in _SOIL_TO_VALUE:
            raise HomeAssistantError(f"Invalid soil option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_WM_SOIL] = _SOIL_TO_VALUE[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _SOIL_OPTIONS:
            self._current = last.state
            self._entry_data[DATA_KEY_WM_SOIL] = _SOIL_TO_VALUE[self._current]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                self._on_program_changed,
            )
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        option = _SOIL_FROM_VALUE.get(prog.soil_level, "None")
        self._current = option
        self._entry_data[DATA_KEY_WM_SOIL] = _SOIL_TO_VALUE[option]
        self.async_write_ha_state()


class CandyWashSteamSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._current = "Off"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_STEAM.format(self.config_id)

    @property
    def name(self) -> str:
        return "04 Steam"

    @property
    def options(self) -> list[str]:
        return _STEAM_OPTIONS

    @property
    def current_option(self) -> str:
        return self._current

    @property
    def icon(self) -> str:
        return "mdi:weather-fog"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_WASHING_MACHINE,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_KITCHEN,
        )

    async def async_select_option(self, option: str) -> None:
        if option not in _STEAM_TO_VALUE:
            raise HomeAssistantError(f"Invalid steam option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_WM_STEAM] = _STEAM_TO_VALUE[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _STEAM_OPTIONS:
            self._current = last.state
            self._entry_data[DATA_KEY_WM_STEAM] = _STEAM_TO_VALUE[self._current]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                self._on_program_changed,
            )
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        option = _STEAM_FROM_VALUE.get(prog.steam, "Off")
        self._current = option
        self._entry_data[DATA_KEY_WM_STEAM] = _STEAM_TO_VALUE[option]
        self.async_write_ha_state()


class CandyTumbleProgramSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str):
        self.config_id = config_id
        self._current_option = TUMBLE_DRYER_PROGRAMS[0].name

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_PROGRAM_SELECT.format(self.config_id)

    @property
    def name(self) -> str:
        return "01 Program"

    @property
    def options(self) -> list[str]:
        return sorted((p.name for p in TUMBLE_DRYER_PROGRAMS), key=str.casefold)

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def icon(self) -> str:
        return "mdi:tumble-dryer"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_TUMBLE_DRYER,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_BATHROOM,
        )

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self.options:
            self._current_option = last_state.state
