"""Select entities for Candy washing machine program selection."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .client.model import WashingMachineStatus
from .const import (DATA_KEY_COORDINATOR, DEVICE_NAME_WASHING_MACHINE,
                    DOMAIN, SUGGESTED_AREA_KITCHEN)
from .programs import WASHING_MACHINE_PROGRAMS

UNIQUE_ID_WM_PROGRAM_SELECT = "{0}-wm_program_select"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([CandyWashProgramSelect(config_id)])


class CandyWashProgramSelect(RestoreEntity, SelectEntity):

    def __init__(self, config_id: str):
        self.config_id = config_id
        self._current_option = WASHING_MACHINE_PROGRAMS[0].name

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_PROGRAM_SELECT.format(self.config_id)

    @property
    def name(self) -> str:
        return "Washing machine program"

    @property
    def options(self) -> list[str]:
        return [p.name for p in WASHING_MACHINE_PROGRAMS]

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
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self.options:
            self._current_option = last_state.state
