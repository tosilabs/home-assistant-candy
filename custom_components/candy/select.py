"""Select entities for Candy program selection and wash settings.

Display order in HA device page is determined by the unique_id prefix:
  s01 → Category
  s02 → Program
  s03 → Temperature
  s04 → Spin speed
  s05 → Soil level
  s06 → Steam
  s07 → Rinse
"""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .client.model import TumbleDryerStatus, WashingMachineStatus
from .const import (
    DATA_KEY_COORDINATOR,
    DATA_KEY_TD_CATEGORY,
    DATA_KEY_TD_DRY_LEVEL,
    DATA_KEY_WM_CATEGORY,
    DATA_KEY_WM_RINSE,
    DATA_KEY_WM_SOIL,
    DATA_KEY_WM_SPIN,
    DATA_KEY_WM_STEAM,
    DATA_KEY_WM_TEMP,
    DEVICE_NAME_TUMBLE_DRYER,
    DEVICE_NAME_WASHING_MACHINE,
    DOMAIN,
    SIGNAL_TD_CATEGORY_CHANGED,
    SIGNAL_TD_PROGRAM_CHANGED,
    SIGNAL_WM_CATEGORY_CHANGED,
    SIGNAL_WM_PROGRAM_CHANGED,
    SUGGESTED_AREA_BATHROOM,
    SUGGESTED_AREA_KITCHEN,
    UNIQUE_ID_TD_DRY_LEVEL_SELECT,
    UNIQUE_ID_WM_CATEGORY_SELECT,
    UNIQUE_ID_WM_PROGRAM_SELECT_V2,
    UNIQUE_ID_WM_RINSE,
    UNIQUE_ID_WM_SOIL,
    UNIQUE_ID_WM_SPIN_SELECT,
    UNIQUE_ID_WM_STEAM,
    UNIQUE_ID_WM_TEMP_SELECT,
)
from .programs import (
    TUMBLE_DRYER_PROGRAMS,
    TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ,
    TUMBLE_DRYER_PROGRAM_META_SQ,
    WASHING_MACHINE_PROGRAMS,
    WASHING_MACHINE_PROGRAMS_BY_NAME,
    WASHING_MACHINE_PROGRAM_DESCRIPTIONS_SQ,
    WASHING_MACHINE_PROGRAM_META_SQ,
)

# ---------------------------------------------------------------------------
# Legacy unique_id kept for backwards compatibility with button.py imports
# ---------------------------------------------------------------------------
UNIQUE_ID_WM_PROGRAM_SELECT = UNIQUE_ID_WM_PROGRAM_SELECT_V2
UNIQUE_ID_TD_PROGRAM_SELECT = "{0}-s01_td_program"

# ---------------------------------------------------------------------------
# Soil level
# ---------------------------------------------------------------------------
_SOIL_OPTIONS = ["None", "Light", "Medium", "Heavy"]
_SOIL_TO_VALUE = {"None": None, "Light": 1, "Medium": 2, "Heavy": 3}
_SOIL_FROM_VALUE = {None: "None", 0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}

# ---------------------------------------------------------------------------
# Steam
# ---------------------------------------------------------------------------
_STEAM_OPTIONS = ["Off", "Low", "High"]
_STEAM_TO_VALUE = {"Off": 0, "Low": 1, "High": 2}
_STEAM_FROM_VALUE = {0: "Off", 1: "Low", 2: "High"}

# ---------------------------------------------------------------------------
# Rinse (extra rinse cycles: 0 = normal, 1 = +1, 2 = +2, 3 = +3)
# ---------------------------------------------------------------------------
_RINSE_OPTIONS = ["Normal", "+1", "+2", "+3"]
_RINSE_TO_VALUE = {"Normal": 0, "+1": 1, "+2": 2, "+3": 3}
_RINSE_FROM_VALUE = {0: "Normal", 1: "+1", 2: "+2", 3: "+3"}

# ---------------------------------------------------------------------------
# Tumble dryer dry level
# ---------------------------------------------------------------------------
_TD_DRY_LEVEL_OPTIONS = ["Auto", "Iron dry", "Dry hanger", "Dry wardrobe", "Extra dry"]
_TD_DRY_LEVEL_TO_VALUE = {"Auto": 0, "Iron dry": 1, "Dry hanger": 2, "Dry wardrobe": 3, "Extra dry": 4}
_TD_DRY_LEVEL_FROM_VALUE = {v: k for k, v in _TD_DRY_LEVEL_TO_VALUE.items()}

# ---------------------------------------------------------------------------
# Valid Candy wash temperatures (°C) and spin speeds (rpm, full values)
#
# IMPORTANT — Candy API encoding:
#   spin_target in WashProgram is stored as rpm // 100
#   e.g. spin_target=14 → 1400 rpm,  spin_target=8 → 800 rpm
#   Always multiply by 100 before comparing with _VALID_SPINS.
#
#   temp in WashProgram is the DEFAULT temperature for that program.
#   It is NOT a maximum — users can freely choose any valid temperature.
#   We show all temperatures up to 90°C regardless of program default.
# ---------------------------------------------------------------------------
_VALID_TEMPS = [0, 20, 30, 40, 60, 90]
_TEMP_LABELS = {0: "Cold", 20: "20°C", 30: "30°C", 40: "40°C", 60: "60°C", 90: "90°C"}
_TEMP_FROM_LABEL = {v: k for k, v in _TEMP_LABELS.items()}

_VALID_SPINS = [0, 400, 600, 800, 900, 1000, 1200, 1400, 1500]
_SPIN_LABELS = {
    0: "No spin", 400: "400 rpm", 600: "600 rpm", 800: "800 rpm",
    900: "900 rpm", 1000: "1000 rpm", 1200: "1200 rpm",
    1400: "1400 rpm", 1500: "1500 rpm",
}
_SPIN_FROM_LABEL = {v: k for k, v in _SPIN_LABELS.items()}

# All temperature / spin option lists (static, shown as-is)
_ALL_TEMP_OPTIONS: list[str] = [_TEMP_LABELS[t] for t in _VALID_TEMPS]
_ALL_SPIN_OPTIONS: list[str] = [_SPIN_LABELS[s] for s in _VALID_SPINS]


def _decoded_spin_rpm(prog) -> int | None:
    """Return spin speed in full RPM, decoding the Candy encoded value (rpm//100)."""
    enc = getattr(prog, "spin_target", None)
    if enc is None:
        return None
    # Values ≤ 20 are encoded (rpm//100); larger values are already in rpm
    return enc * 100 if enc <= 20 else enc


def _spin_options_for_program(prog) -> list[str]:
    """Return all spin labels up to the program's maximum spin speed.

    spin_target on WashProgram is the DEFAULT (and effectively max) speed
    in Candy-encoded units (rpm // 100).  We decode it first, then filter.
    If spin_target is None the machine supports all speeds.
    """
    max_rpm = _decoded_spin_rpm(prog)
    if max_rpm is None:
        return _ALL_SPIN_OPTIONS
    return [_SPIN_LABELS[s] for s in _VALID_SPINS if s <= max_rpm]


def _temp_options_for_program(_prog) -> list[str]:
    """Return all standard temperature options.

    The WashProgram.temp field is only the *default* temperature, not a
    hard maximum — the user should be free to pick any Candy-valid temp.
    """
    return _ALL_TEMP_OPTIONS


# ---------------------------------------------------------------------------
# Pre-compute program lists grouped by category (static at import time)
# ---------------------------------------------------------------------------
_WM_PROGRAMS_BY_CATEGORY: dict[str, list[str]] = {}
for _prog in WASHING_MACHINE_PROGRAMS:
    _cat = WASHING_MACHINE_PROGRAM_META_SQ.get(_prog.name, {}).get("category", "Tjetër")
    _WM_PROGRAMS_BY_CATEGORY.setdefault(_cat, []).append(_prog.name)
_WM_ALL_PROGRAMS: list[str] = sorted(
    [p.name for p in WASHING_MACHINE_PROGRAMS], key=str.casefold
)

_TD_PROGRAMS_BY_CATEGORY: dict[str, list[str]] = {}
for _prog in TUMBLE_DRYER_PROGRAMS:
    _cat = TUMBLE_DRYER_PROGRAM_META_SQ.get(_prog.name, {}).get("category", "Tjetër")
    _TD_PROGRAMS_BY_CATEGORY.setdefault(_cat, []).append(_prog.name)
_TD_ALL_PROGRAMS: list[str] = sorted(
    [p.name for p in TUMBLE_DRYER_PROGRAMS], key=str.casefold
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]
    entry_data = hass.data[DOMAIN][config_id]

    entry_data.setdefault(DATA_KEY_WM_TEMP, None)
    entry_data.setdefault(DATA_KEY_WM_SPIN, None)
    entry_data.setdefault(DATA_KEY_WM_SOIL, None)
    entry_data.setdefault(DATA_KEY_WM_STEAM, 0)
    entry_data.setdefault(DATA_KEY_WM_RINSE, 0)

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashCategorySelect(config_id, entry_data, coordinator),
            CandyWashProgramSelect(config_id, entry_data, coordinator),
            CandyWashTemperatureSelect(config_id, entry_data, coordinator),
            CandyWashSpinSelect(config_id, entry_data, coordinator),
            CandyWashSoilLevelSelect(config_id, entry_data, coordinator),
            CandyWashSteamSelect(config_id, entry_data, coordinator),
            CandyWashRinseSelect(config_id, entry_data, coordinator),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumbleCategorySelect(config_id, entry_data, coordinator),
            CandyTumbleProgramSelect(config_id, entry_data, coordinator),
            CandyTumbleDryLevelSelect(config_id, entry_data, coordinator),
        ])


# ===========================================================================
# Base class
# ===========================================================================

class _CandySelectBase(RestoreEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, config_id: str, entry_data: dict, coordinator: DataUpdateCoordinator):
        self.config_id = config_id
        self._entry_data = entry_data
        self._coordinator = coordinator

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


# ===========================================================================
# WM — s01 Category
# ===========================================================================

class CandyWashCategorySelect(_CandySelectBase):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "All"

    @property
    def unique_id(self): return UNIQUE_ID_WM_CATEGORY_SELECT.format(self.config_id)

    @property
    def name(self): return "Category"

    @property
    def options(self) -> list[str]:
        cats = {m.get("category", "Tjetër") for m in WASHING_MACHINE_PROGRAM_META_SQ.values()}
        return ["All", *sorted(cats)]

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:shape-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

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


# ===========================================================================
# WM — s02 Program
# ===========================================================================

class CandyWashProgramSelect(_CandySelectBase):

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current_option = WASHING_MACHINE_PROGRAMS[0].name

    @property
    def unique_id(self): return UNIQUE_ID_WM_PROGRAM_SELECT_V2.format(self.config_id)

    @property
    def name(self): return "Program"

    @property
    def options(self) -> list[str]:
        cat = self._entry_data.get(DATA_KEY_WM_CATEGORY, "All")
        if cat == "All":
            return _WM_ALL_PROGRAMS
        return sorted(_WM_PROGRAMS_BY_CATEGORY.get(cat, []), key=str.casefold)

    @property
    def current_option(self): return self._current_option

    @property
    def icon(self): return "mdi:washing-machine"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "category_sq": WASHING_MACHINE_PROGRAM_META_SQ.get(self._current_option, {}).get("category", "Tjetër"),
            "profile_sq": WASHING_MACHINE_PROGRAM_META_SQ.get(self._current_option, {}).get("profile", "Profil i panjohur"),
            "description_sq": WASHING_MACHINE_PROGRAM_DESCRIPTIONS_SQ.get(
                self._current_option,
                "Përshkrimi në shqip nuk është shtuar ende për këtë program.",
            ),
        }

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self._entry_data["wm_program_name"] = option
        prog = WASHING_MACHINE_PROGRAMS_BY_NAME.get(option)
        if prog:
            from homeassistant.helpers.dispatcher import async_dispatcher_send
            async_dispatcher_send(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id), prog)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            self._current_option = last.state
        elif self.options:
            self._current_option = self.options[0]
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_WM_CATEGORY_CHANGED.format(self.config_id),
                                     self._on_category_changed)
        )

    @callback
    def _on_category_changed(self, _cat: str) -> None:
        if self._current_option not in self.options and self.options:
            self._current_option = self.options[0]
            self._entry_data["wm_program_name"] = self._current_option
        self.async_write_ha_state()


# ===========================================================================
# WM — s03 Temperature
# ===========================================================================

class CandyWashTemperatureSelect(_CandySelectBase):
    """Temperature select — shows ALL valid Candy temps (0–90°C).
    The program default is pre-selected when user changes program,
    but the user can override to any value freely.
    """

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "40°C"

    @property
    def unique_id(self): return UNIQUE_ID_WM_TEMP_SELECT.format(self.config_id)

    @property
    def name(self): return "Temperature"

    @property
    def options(self) -> list[str]:
        return _ALL_TEMP_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:thermometer"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

    async def async_select_option(self, option: str) -> None:
        if option not in _TEMP_FROM_LABEL:
            raise HomeAssistantError(f"Invalid temperature option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_WM_TEMP] = _TEMP_FROM_LABEL[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _TEMP_FROM_LABEL:
            self._current = last.state
            self._entry_data[DATA_KEY_WM_TEMP] = _TEMP_FROM_LABEL[self._current]
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        """Pre-select program's default temperature."""
        temp_val = getattr(prog, "temp", None)
        if temp_val is not None and temp_val not in (0, 255):
            nearest = min(_VALID_TEMPS, key=lambda t: abs(t - temp_val))
            label = _TEMP_LABELS.get(nearest, "40°C")
        elif temp_val == 0:
            label = "Cold"
        else:
            label = "40°C"
        self._current = label
        self._entry_data[DATA_KEY_WM_TEMP] = _TEMP_FROM_LABEL.get(label, 40)
        self.async_write_ha_state()


# ===========================================================================
# WM — s04 Spin speed
# ===========================================================================

class CandyWashSpinSelect(_CandySelectBase):
    """Spin speed select.

    Shows all speeds up to the program's max (spin_target decoded from rpm//100).
    Pre-selects the program default when user changes program.
    """

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "1000 rpm"

    @property
    def unique_id(self): return UNIQUE_ID_WM_SPIN_SELECT.format(self.config_id)

    @property
    def name(self): return "Spin speed"

    @property
    def options(self) -> list[str]:
        prog_name = self._entry_data.get("wm_program_name")
        prog = WASHING_MACHINE_PROGRAMS_BY_NAME.get(prog_name) if prog_name else None
        if prog:
            opts = _spin_options_for_program(prog)
            return opts if opts else _ALL_SPIN_OPTIONS
        return _ALL_SPIN_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:rotate-right"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

    async def async_select_option(self, option: str) -> None:
        if option not in _SPIN_FROM_LABEL:
            raise HomeAssistantError(f"Invalid spin option: {option}")
        self._current = option
        rpm = _SPIN_FROM_LABEL[option]
        self._entry_data[DATA_KEY_WM_SPIN] = rpm // 100  # encode back to Candy format
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _SPIN_FROM_LABEL:
            self._current = last.state
            self._entry_data[DATA_KEY_WM_SPIN] = _SPIN_FROM_LABEL[self._current] // 100
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        """Pre-select program default spin, clamped to available options."""
        rpm = _decoded_spin_rpm(prog)
        if rpm is not None:
            nearest = min(_VALID_SPINS, key=lambda s: abs(s - rpm))
            label = _SPIN_LABELS.get(nearest, "1000 rpm")
        else:
            label = "1000 rpm"
        # Clamp to available options for this program
        opts = _spin_options_for_program(prog)
        if opts and label not in opts:
            label = opts[-1]
        self._current = label
        self._entry_data[DATA_KEY_WM_SPIN] = _SPIN_FROM_LABEL.get(label, 1000) // 100
        self.async_write_ha_state()


# ===========================================================================
# WM — s05 Soil level
# ===========================================================================

class CandyWashSoilLevelSelect(_CandySelectBase):

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "Medium"

    @property
    def unique_id(self): return UNIQUE_ID_WM_SOIL.format(self.config_id)

    @property
    def name(self): return "Soil level"

    @property
    def options(self): return _SOIL_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:water-opacity"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

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
            async_dispatcher_connect(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        option = _SOIL_FROM_VALUE.get(getattr(prog, "soil_level", None), "None")
        self._current = option
        self._entry_data[DATA_KEY_WM_SOIL] = _SOIL_TO_VALUE[option]
        self.async_write_ha_state()


# ===========================================================================
# WM — s06 Steam
# ===========================================================================

class CandyWashSteamSelect(_CandySelectBase):

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "Off"

    @property
    def unique_id(self): return UNIQUE_ID_WM_STEAM.format(self.config_id)

    @property
    def name(self): return "Steam"

    @property
    def options(self): return _STEAM_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:weather-fog"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

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
            async_dispatcher_connect(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        option = _STEAM_FROM_VALUE.get(getattr(prog, "steam", 0), "Off")
        self._current = option
        self._entry_data[DATA_KEY_WM_STEAM] = _STEAM_TO_VALUE[option]
        self.async_write_ha_state()


# ===========================================================================
# WM — s07 Rinse
# ===========================================================================

class CandyWashRinseSelect(_CandySelectBase):

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "Normal"

    @property
    def unique_id(self): return UNIQUE_ID_WM_RINSE.format(self.config_id)

    @property
    def name(self): return "Rinse"

    @property
    def options(self): return _RINSE_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:water-sync"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_WASHING_MACHINE, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_KITCHEN)

    async def async_select_option(self, option: str) -> None:
        if option not in _RINSE_TO_VALUE:
            raise HomeAssistantError(f"Invalid rinse option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_WM_RINSE] = _RINSE_TO_VALUE[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _RINSE_OPTIONS:
            self._current = last.state
            self._entry_data[DATA_KEY_WM_RINSE] = _RINSE_TO_VALUE[self._current]
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_WM_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        self._current = "Normal"
        self._entry_data[DATA_KEY_WM_RINSE] = 0
        self.async_write_ha_state()


# ===========================================================================
# TD — s01 Category
# ===========================================================================

class CandyTumbleCategorySelect(_CandySelectBase):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "All"

    @property
    def unique_id(self): return f"{self.config_id}-s01_td_category"

    @property
    def name(self): return "Category"

    @property
    def options(self) -> list[str]:
        cats = {m.get("category", "Tjetër") for m in TUMBLE_DRYER_PROGRAM_META_SQ.values()}
        return ["All", *sorted(cats)]

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:shape-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_TUMBLE_DRYER, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_BATHROOM)

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


# ===========================================================================
# TD — s02 Program
# ===========================================================================

class CandyTumbleProgramSelect(_CandySelectBase):

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current_option = TUMBLE_DRYER_PROGRAMS[0].name

    @property
    def unique_id(self): return UNIQUE_ID_TD_PROGRAM_SELECT.format(self.config_id)

    @property
    def name(self): return "Program"

    @property
    def options(self) -> list[str]:
        cat = self._entry_data.get(DATA_KEY_TD_CATEGORY, "All")
        if cat == "All":
            return _TD_ALL_PROGRAMS
        return sorted(_TD_PROGRAMS_BY_CATEGORY.get(cat, []), key=str.casefold)

    @property
    def current_option(self): return self._current_option

    @property
    def icon(self): return "mdi:tumble-dryer"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_TUMBLE_DRYER, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_BATHROOM)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "category_sq": TUMBLE_DRYER_PROGRAM_META_SQ.get(self._current_option, {}).get("category", "Tjetër"),
            "profile_sq": TUMBLE_DRYER_PROGRAM_META_SQ.get(self._current_option, {}).get("profile", "Profil i panjohur"),
            "description_sq": TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ.get(
                self._current_option,
                "Përshkrimi në shqip nuk është shtuar ende për këtë program.",
            ),
        }

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        from homeassistant.helpers.dispatcher import async_dispatcher_send
        from .programs import TUMBLE_DRYER_PROGRAMS_BY_NAME
        prog = TUMBLE_DRYER_PROGRAMS_BY_NAME.get(option)
        if prog:
            async_dispatcher_send(self.hass, SIGNAL_TD_PROGRAM_CHANGED.format(self.config_id), prog)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            self._current_option = last.state
        elif self.options:
            self._current_option = self.options[0]
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_TD_CATEGORY_CHANGED.format(self.config_id),
                                     self._on_category_changed)
        )

    @callback
    def _on_category_changed(self, _cat: str) -> None:
        if self._current_option not in self.options and self.options:
            self._current_option = self.options[0]
        self.async_write_ha_state()


# ===========================================================================
# TD — s03 Dry level
# ===========================================================================

class CandyTumbleDryLevelSelect(_CandySelectBase):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, config_id, entry_data, coordinator):
        super().__init__(config_id, entry_data, coordinator)
        self._current = "Auto"

    @property
    def unique_id(self): return UNIQUE_ID_TD_DRY_LEVEL_SELECT.format(self.config_id)

    @property
    def name(self): return "Drying level"

    @property
    def options(self): return _TD_DRY_LEVEL_OPTIONS

    @property
    def current_option(self): return self._current

    @property
    def icon(self): return "mdi:tumble-dryer-alert"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.config_id)},
                         name=DEVICE_NAME_TUMBLE_DRYER, manufacturer="Candy",
                         suggested_area=SUGGESTED_AREA_BATHROOM)

    async def async_select_option(self, option: str) -> None:
        if option not in _TD_DRY_LEVEL_TO_VALUE:
            raise HomeAssistantError(f"Invalid dry level option: {option}")
        self._current = option
        self._entry_data[DATA_KEY_TD_DRY_LEVEL] = _TD_DRY_LEVEL_TO_VALUE[option]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in _TD_DRY_LEVEL_OPTIONS:
            self._current = last.state
            self._entry_data[DATA_KEY_TD_DRY_LEVEL] = _TD_DRY_LEVEL_TO_VALUE[self._current]
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_TD_PROGRAM_CHANGED.format(self.config_id),
                                     self._on_program_changed)
        )

    @callback
    def _on_program_changed(self, prog) -> None:
        dry_val = getattr(prog, "dry_level", None)
        option = _TD_DRY_LEVEL_FROM_VALUE.get(dry_val, "Auto")
        self._current = option
        self._entry_data[DATA_KEY_TD_DRY_LEVEL] = _TD_DRY_LEVEL_TO_VALUE[option]
        self.async_write_ha_state()
