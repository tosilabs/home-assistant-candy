"""Exercise category selection, restore and Start using real HA dispatching."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.candy.const import (
    DATA_KEY_WM_CATEGORY, DATA_KEY_WM_SPIN, DATA_KEY_WM_TEMP,
    SIGNAL_WM_PROGRAM_CHANGED,
)
from custom_components.candy.select import (
    CandyWashProgramSelect, CandyWashTemperatureSelect, CandyWashSpinSelect,
    _WM_PROGRAMS_BY_CATEGORY,
)
from custom_components.candy.wash_settings import select_wash_program


def entity(cls, hass, data):
    instance = cls("test", data, SimpleNamespace(last_update_success=True))
    instance.hass = hass
    instance.async_write_ha_state = MagicMock()
    return instance


async def test_category_change_resets_settings_and_notifies_controls(hass):
    data = {}
    select_wash_program(data, "Trainers")
    data.update(wm_temp=90, wm_spin=15, wm_steam=2, wm_soil=3)
    program = entity(CandyWashProgramSelect, hass, data)
    program._current_option = "Trainers"
    callback = MagicMock()
    unsub = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), callback)
    try:
        category = next(cat for cat, names in _WM_PROGRAMS_BY_CATEGORY.items() if "Trainers" not in names)
        data[DATA_KEY_WM_CATEGORY] = category
        program._on_category_changed(category)
        await hass.async_block_till_done()
        assert data["wm_program_name"] == program.current_option
        assert data["wm_temp"] != 90
        callback.assert_called_once()
    finally:
        unsub()


async def test_direct_recipe_selection_updates_controls(hass):
    data = {}
    program = entity(CandyWashProgramSelect, hass, data)
    temp = entity(CandyWashTemperatureSelect, hass, data)
    spin = entity(CandyWashSpinSelect, hass, data)
    unsub_temp = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), temp._on_program_changed)
    unsub_spin = async_dispatcher_connect(hass, SIGNAL_WM_PROGRAM_CHANGED.format("test"), spin._on_program_changed)
    try:
        await program.async_select_option("Trainers")
        await hass.async_block_till_done()
        assert temp.current_option == "20°C"
        assert spin.current_option == "400 rpm"
        with pytest.raises(HomeAssistantError):
            await spin.async_select_option("1500 rpm")
        assert data[DATA_KEY_WM_SPIN] == 4
    finally:
        unsub_temp()
        unsub_spin()


async def test_missing_temperature_default_is_not_changed_to_40(hass):
    data = {}
    select_wash_program(data, "Perfect 20")
    temp = entity(CandyWashTemperatureSelect, hass, data)
    from custom_components.candy.programs import WASHING_MACHINE_PROGRAMS_BY_NAME
    temp._on_program_changed(WASHING_MACHINE_PROGRAMS_BY_NAME["Perfect 20"])
    assert temp.current_option == "Program default"
    assert data[DATA_KEY_WM_TEMP] is None
