"""Select entities for Candy program selection and wash settings."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import (DATA_KEY_COORDINATOR, DATA_KEY_TD_CATEGORY, DATA_KEY_TD_DRY_LEVEL, DATA_KEY_WM_CATEGORY, DATA_KEY_WM_SOIL, DATA_KEY_WM_STEAM,
                    DEVICE_NAME_TUMBLE_DRYER, DEVICE_NAME_WASHING_MACHINE, DOMAIN,
                    SIGNAL_WM_PROGRAM_CHANGED, SUGGESTED_AREA_BATHROOM,
                    SUGGESTED_AREA_KITCHEN, UNIQUE_ID_WM_SOIL, UNIQUE_ID_WM_STEAM)
from .programs import (TUMBLE_DRYER_PROGRAMS,
                       TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ,
                       TUMBLE_DRYER_PROGRAM_META_SQ,
                       WASHING_MACHINE_PROGRAMS,
                       WASHING_MACHINE_PROGRAMS_BY_NAME,
                       WASHING_MACHINE_PROGRAM_DESCRIPTIONS_SQ,
                       WASHING_MACHINE_PROGRAM_META_SQ)

UNIQUE_ID_WM_PROGRAM_SELECT = "{0}-wm_program_select"
UNIQUE_ID_TD_PROGRAM_SELECT = "{0}-td_program_select"

_SOIL_OPTIONS = ["None", "Light", "Medium", "Heavy"]
_SOIL_TO_VALUE = {"None": None, "Light": 1, "Medium": 2, "Heavy": 3}
_SOIL_FROM_VALUE = {None: "None", 0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}

_STEAM_OPTIONS = ["Off", "Low", "High"]
_STEAM_TO_VALUE = {"Off": 0, "Low": 1, "High": 2}
_STEAM_FROM_VALUE = {0: "Off", 1: "Low", 2: "High"}
_TD_DRY_LEVEL_OPTIONS = ["Auto", "Iron dry", "Dry hanger", "Dry wardrobe", "Extra dry"]
_TD_DRY_LEVEL_TO_VALUE = {"Auto": 0, "Iron dry": 1, "Dry hanger": 2, "Dry wardrobe": 3, "Extra dry": 4}
_TD_DRY_LEVEL_FROM_VALUE = {v: k for k, v in _TD_DRY_LEVEL_TO_VALUE.items()}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]
    entry_data = hass.data[DOMAIN][config_id]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashCategorySelect(config_id, entry_data),
            CandyWashProgramSelect(config_id, entry_data),
            CandyWashSoilLevelSelect(config_id, entry_data),
            CandyWashSteamSelect(config_id, entry_data),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumbleCategorySelect(config_id, entry_data),
            CandyTumbleProgramSelect(config_id, entry_data),
            CandyTumbleDryLevelSelect(config_id, entry_data),
        ])


class CandyWashProgramSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
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

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "category_sq": WASHING_MACHINE_PROGRAM_META_SQ.get(self._current_option, {}).get("category", "Tjetër"),
            "profile_sq": WASHING_MACHINE_PROGRAM_META_SQ.get(self._current_option, {}).get("profile", "Profil i panjohur"),
            "description_sq": WASHING_MACHINE_PROGRAM_DESCRIPTIONS_SQ.get(
                self._current_option,
                "Përshkrimi në shqip nuk është shtuar ende për këtë program.",
            )
        }

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self._entry_data["wm_program_name"] = option
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
        elif self.options:
            self._current_option = self.options[0]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_WM_CATEGORY_CHANGED.format(self.config_id),
                self._on_category_changed,
            )
        )

    @callback
    def _on_category_changed(self, _category: str) -> None:
        if self._current_option not in self.options and self.options:
            self._current_option = self.options[0]
            self._entry_data["wm_program_name"] = self._current_option
        self.async_write_ha_state()


class CandyWashCategorySelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._current = "1. Cycles"

    @property
    def unique_id(self) -> str:
        return f"{self.config_id}-wm_category_select"

    @property
    def name(self) -> str:
        return "Category"

    @property
    def options(self) -> list[str]:
        categories = {meta.get("category", "Tjetër") for meta in WASHING_MACHINE_PROGRAM_META_SQ.values()}
        return sorted(categories)

    @property
    def current_option(self) -> str:
        return self._current

    @property
    def icon(self) -> str:
        return "mdi:shape-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_WASHING_MACHINE,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_KITCHEN,
        )

    async def async_select_option(self, option: str) -> None:
        self._current = option
        self._entry_data[DATA_KEY_WM_CATEGORY] = option
        from homeassistant.helpers.dispatcher import async_dispatcher_send
        async_dispatcher_send(self.hass, SIGNAL_WM_CATEGORY_CHANGED.format(self.config_id), option)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            self._current = last.state
        self._entry_data[DATA_KEY_WM_CATEGORY] = self._current


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


class CandyTumbleCategorySelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._current = "1. Cycles"

    @property
    def unique_id(self) -> str:
        return f"{self.config_id}-td_category_select"

    @property
    def name(self) -> str:
        return "Category"

    @property
    def options(self) -> list[str]:
        categories = {meta.get("category", "Tjetër") for meta in TUMBLE_DRYER_PROGRAM_META_SQ.values()}
        return sorted(categories)

    @property
    def current_option(self) -> str:
        return self._current

    @property
    def icon(self) -> str:
        return "mdi:shape-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_TUMBLE_DRYER,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_BATHROOM,
        )

    async def async_select_option(self, option: str) -> None:
        self._current = option
        self._entry_data[DATA_KEY_TD_CATEGORY] = option
        from homeassistant.helpers.dispatcher import async_dispatcher_send
        async_dispatcher_send(self.hass, SIGNAL_TD_CATEGORY_CHANGED.format(self.config_id), option)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            self._current = last.state
        self._entry_data[DATA_KEY_TD_CATEGORY] = self._current


class CandyTumbleProgramSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
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

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "category_sq": TUMBLE_DRYER_PROGRAM_META_SQ.get(self._current_option, {}).get("category", "Tjetër"),
            "profile_sq": TUMBLE_DRYER_PROGRAM_META_SQ.get(self._current_option, {}).get("profile", "Profil i panjohur"),
            "description_sq": TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ.get(
                self._current_option,
                "Përshkrimi në shqip nuk është shtuar ende për këtë program.",
            )
        }

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self.options:
            self._current_option = last_state.state
        elif self.options:
            self._current_option = self.options[0]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_TD_CATEGORY_CHANGED.format(self.config_id),
                self._on_category_changed,
            )
        )

    @callback
    def _on_category_changed(self, _category: str) -> None:
        if self._current_option not in self.options and self.options:
            self._current_option = self.options[0]
        self.async_write_ha_state()


class CandyTumbleDryLevelSelect(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id: str, entry_data: dict):
        self.config_id = config_id
        self._entry_data = entry_data
        self._current = "Auto"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_DRY_LEVEL_SELECT.format(self.config_id)

    @property
    def name(self) -> str:
        return "Drying level"

    @property
    def options(self) -> list[str]:
        return _TD_DRY_LEVEL_OPTIONS

    @property
    def current_option(self) -> str:
        return self._current

    @property
    def icon(self) -> str:
        return "mdi:tumble-dryer-alert"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=DEVICE_NAME_TUMBLE_DRYER,
            manufacturer="Candy",
            suggested_area=SUGGESTED_AREA_BATHROOM,
        )

    async def async_select_option(self, option: str) -> None:
        if option not in _TD_DRY_LEVEL_TO_VALUE:
            raise HomeAssistantError(f"Invalid dry level option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_TD_DRY_LEVEL] = _TD_DRY_LEVEL_TO_VALUE[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            self._current = last.state
            self._entry_data[DATA_KEY_TD_DRY_LEVEL] = _TD_DRY_LEVEL_TO_VALUE[self._current]
