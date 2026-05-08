from abc import abstractmethod
from typing import Any, Mapping, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .client import WashingMachineStatus
from .client.model import (DishwasherState, DishwasherStatus,
                           DryerCycleState, DryerProgramState, MachineState,
                           OvenStatus, TumbleDryerStatus, WashProgramState)
from .const import *

_SOIL_LABELS = {0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the Candy sensors from config entry."""

    config_id = config_entry.entry_id
    coordinator = hass.data[DOMAIN][config_id][DATA_KEY_COORDINATOR]

    if isinstance(coordinator.data, WashingMachineStatus):
        async_add_entities([
            CandyWashingMachineSensor(coordinator, config_id),
            CandyWashCycleStatusSensor(coordinator, config_id),
            CandyWashRemainingTimeSensor(coordinator, config_id),
            CandyWashProgramSensor(coordinator, config_id),
            CandyWashTemperatureSensor(coordinator, config_id),
            CandyWashSpinSensor(coordinator, config_id),
            CandyWashSoilLevelSensor(coordinator, config_id),
            CandyWashErrorSensor(coordinator, config_id),
            CandyWashDelayStartSensor(coordinator, config_id),
        ])
    elif isinstance(coordinator.data, TumbleDryerStatus):
        async_add_entities([
            CandyTumbleDryerSensor(coordinator, config_id),
            CandyTumbleStatusSensor(coordinator, config_id),
            CandyTumbleRemainingTimeSensor(coordinator, config_id),
            CandyTumbleDryLevelSensor(coordinator, config_id),
            CandyTumbleErrorSensor(coordinator, config_id),
            CandyTumbleDelayStartSensor(coordinator, config_id),
        ])
    elif isinstance(coordinator.data, OvenStatus):
        async_add_entities([
            CandyOvenSensor(coordinator, config_id),
            CandyOvenTempSensor(coordinator, config_id)
        ])
    elif isinstance(coordinator.data, DishwasherStatus):
        async_add_entities([
            CandyDishwasherSensor(coordinator, config_id),
            CandyDishwasherRemainingTimeSensor(coordinator, config_id)
        ])
    else:
        raise Exception(f"Unable to determine machine type: {coordinator.data}")


class CandyBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, config_id: str):
        super().__init__(coordinator)
        self.config_id = config_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_id)},
            name=self.device_name(),
            manufacturer="Candy",
            suggested_area=self.suggested_area(),
        )

    @abstractmethod
    def device_name(self) -> str:
        pass

    @abstractmethod
    def suggested_area(self) -> str:
        pass


# ── Washing machine ────────────────────────────────────────────────────────────

class CandyWashingMachineSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_WASHING_MACHINE

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Machine status"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASHING_MACHINE.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        return str(status.machine_state)

    @property
    def icon(self) -> str:
        return "mdi:washing-machine"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        status: WashingMachineStatus = self.coordinator.data

        attributes: dict = {
            "program": status.program,
            "remote_control": status.remote_control,
        }

        if status.machine_state not in (MachineState.IDLE, MachineState.FINISHED1, MachineState.FINISHED2):
            if status.program_type is not None:
                attributes["program_type"] = str(status.program_type)

        if status.temp is not None:
            attributes["temperature"] = status.temp
        if status.spin_speed is not None:
            attributes["spin_speed"] = status.spin_speed

        if status.machine_state in (MachineState.RUNNING, MachineState.PAUSED):
            attributes["remaining_minutes"] = status.remaining_minutes
        else:
            attributes["remaining_minutes"] = 0

        if status.fill_percent is not None:
            attributes["fill_percent"] = status.fill_percent
        if status.program_code is not None:
            attributes["program_code"] = status.program_code
        if status.delay_start_minutes is not None:
            attributes["delay_start_minutes"] = status.delay_start_minutes

        return attributes


class CandyWashCycleStatusSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_WASHING_MACHINE

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Cycle phase"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_CYCLE_STATUS.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        return str(status.program_state)

    @property
    def icon(self) -> str:
        return "mdi:washing-machine"


class CandyWashRemainingTimeSensor(CandyBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def device_name(self) -> str:
        return DEVICE_NAME_WASHING_MACHINE

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Time remaining"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WASH_REMAINING_TIME.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        if status.machine_state in (MachineState.RUNNING, MachineState.PAUSED):
            return status.remaining_minutes
        return 0

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfTime.MINUTES

    @property
    def icon(self) -> str:
        return "mdi:progress-clock"


# ── Tumble dryer ───────────────────────────────────────────────────────────────

class CandyTumbleDryerSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM

    @property
    def name(self) -> str:
        return "Machine status"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_DRYER.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: TumbleDryerStatus = self.coordinator.data
        return str(status.machine_state)

    @property
    def icon(self) -> str:
        return "mdi:tumble-dryer"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        status: TumbleDryerStatus = self.coordinator.data

        attributes: dict = {
            "program": status.program,
            "remote_control": status.remote_control,
            "refresh": status.refresh,
            "need_clean_filter": status.need_clean_filter,
            "water_tank_full": status.water_tank_full,
            "door_closed": status.door_closed,
        }

        if status.machine_state in (MachineState.RUNNING, MachineState.PAUSED):
            attributes["remaining_minutes"] = status.remaining_minutes
        else:
            attributes["remaining_minutes"] = 0

        if status.dry_level is not None:
            attributes["dry_level"] = status.dry_level
        if status.dry_level_selected is not None:
            attributes["dry_level_now"] = status.dry_level_selected
        if status.delay_start_minutes is not None:
            attributes["delay_start_minutes"] = status.delay_start_minutes

        return attributes


class CandyTumbleStatusSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM

    @property
    def name(self) -> str:
        return "Cycle phase"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_CYCLE_STATUS.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: TumbleDryerStatus = self.coordinator.data
        if status.program_state in (DryerProgramState.STOPPED,):
            return str(status.cycle_state) if status.cycle_state is not None else "Ready"
        return str(status.program_state)

    @property
    def icon(self) -> str:
        return "mdi:tumble-dryer"


class CandyTumbleRemainingTimeSensor(CandyBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def device_name(self) -> str:
        return DEVICE_NAME_TUMBLE_DRYER

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_BATHROOM

    @property
    def name(self) -> str:
        return "Time remaining"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TUMBLE_REMAINING_TIME.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: TumbleDryerStatus = self.coordinator.data
        if status.machine_state in (MachineState.RUNNING, MachineState.PAUSED):
            return status.remaining_minutes
        return 0

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfTime.MINUTES

    @property
    def icon(self) -> str:
        return "mdi:progress-clock"


# ── Oven ───────────────────────────────────────────────────────────────────────

class CandyOvenSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_OVEN

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Machine status"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_OVEN.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: OvenStatus = self.coordinator.data
        return str(status.machine_state)

    @property
    def icon(self) -> str:
        return "mdi:stove"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        status: OvenStatus = self.coordinator.data

        attributes = {
            "program": status.program,
            "selection": status.selection,
            "temperature": status.temp,
            "temperature_reached": status.temp_reached,
            "remote_control": status.remote_control,
        }

        if status.program_length_minutes is not None:
            attributes["program_length_minutes"] = status.program_length_minutes

        return attributes


class CandyOvenTempSensor(CandyBaseSensor):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def device_name(self) -> str:
        return DEVICE_NAME_OVEN

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Oven temperature"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_OVEN_TEMP.format(self.config_id)

    @property
    def native_value(self) -> StateType:
        status: OvenStatus = self.coordinator.data
        return status.temp

    @property
    def icon(self) -> str:
        return "mdi:thermometer"


# ── Dishwasher ─────────────────────────────────────────────────────────────────

class CandyDishwasherSensor(CandyBaseSensor):

    def device_name(self) -> str:
        return DEVICE_NAME_DISHWASHER

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Machine status"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_DISHWASHER.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: DishwasherStatus = self.coordinator.data
        return str(status.machine_state)

    @property
    def icon(self) -> str:
        return "mdi:glass-wine"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        status: DishwasherStatus = self.coordinator.data

        attributes = {
            "program": status.program,
            "remaining_minutes": 0 if status.machine_state in
                                      (DishwasherState.IDLE, DishwasherState.FINISHED) else status.remaining_minutes,
            "remote_control": status.remote_control,
            "door_open": status.door_open,
            "eco_mode": status.eco_mode,
            "salt_empty": status.salt_empty,
            "rinse_aid_empty": status.rinse_aid_empty,
        }

        if status.door_open_allowed is not None:
            attributes["door_open_allowed"] = status.door_open_allowed
        if status.delayed_start_hours is not None:
            attributes["delayed_start_hours"] = status.delayed_start_hours

        return attributes


class CandyDishwasherRemainingTimeSensor(CandyBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def device_name(self) -> str:
        return DEVICE_NAME_DISHWASHER

    def suggested_area(self) -> str:
        return SUGGESTED_AREA_KITCHEN

    @property
    def name(self) -> str:
        return "Time remaining"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_DISHWASHER_REMAINING_TIME.format(self.config_id)

    @property
    def state(self) -> StateType:
        status: DishwasherStatus = self.coordinator.data
        if status.machine_state in (DishwasherState.IDLE, DishwasherState.FINISHED):
            return 0
        return status.remaining_minutes

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfTime.MINUTES

    @property
    def icon(self) -> str:
        return "mdi:progress-clock"


# ── Washing machine – extra sensors ───────────────────────────────────────────

class _WashSensorBase(CandyBaseSensor):
    def device_name(self) -> str: return DEVICE_NAME_WASHING_MACHINE
    def suggested_area(self) -> str: return SUGGESTED_AREA_KITCHEN


class CandyWashProgramSensor(_WashSensorBase):
    @property
    def name(self) -> str: return "Program"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_PROGRAM_SENSOR.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:play-circle"

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        if status.program_state in (WashProgramState.STOPPED, WashProgramState.END):
            return "No Program"
        if status.program_type is None:
            return "Unknown"
        return str(status.program_type)


class CandyWashTemperatureSensor(_WashSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def name(self) -> str: return "Temperature"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_TEMP_SENSOR.format(self.config_id)

    @property
    def native_value(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        if status.machine_state in (MachineState.IDLE, MachineState.FINISHED1, MachineState.FINISHED2):
            return None
        return status.temp


class CandyWashSpinSensor(_WashSensorBase):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "rpm"

    @property
    def name(self) -> str: return "Spin speed"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_SPIN_SENSOR.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:rotate-right"

    @property
    def native_value(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        if status.machine_state in (MachineState.IDLE, MachineState.FINISHED1, MachineState.FINISHED2):
            return None
        return status.spin_speed


class CandyWashSoilLevelSensor(_WashSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str: return "Stain level"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_SOIL_SENSOR.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:water-opacity"

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        if status.soil_level is None:
            return None
        return _SOIL_LABELS.get(status.soil_level, "Unknown")


class CandyWashErrorSensor(_WashSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str: return "Error"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_ERROR.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:alert-circle"

    @property
    def state(self) -> StateType:
        status: WashingMachineStatus = self.coordinator.data
        return status.error


class CandyWashDelayStartSensor(_WashSensorBase):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str: return "Delay start"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_WM_DELAY_START.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:clock-start"

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfTime.MINUTES

    @property
    def state(self) -> StateType:
        return self.coordinator.data.delay_start_minutes


# ── Tumble dryer – extra sensors ──────────────────────────────────────────────

class _TumbleSensorBase(CandyBaseSensor):
    def device_name(self) -> str: return DEVICE_NAME_TUMBLE_DRYER
    def suggested_area(self) -> str: return SUGGESTED_AREA_BATHROOM


class CandyTumbleDryLevelSensor(_TumbleSensorBase):
    @property
    def name(self) -> str: return "Drying level"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_DRY_LEVEL.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:hair-dryer"

    @property
    def state(self) -> StateType:
        status: TumbleDryerStatus = self.coordinator.data
        if status.program_state == DryerProgramState.STOPPED:
            if status.cycle_state is None:
                return None
            return str(status.cycle_state)
        return str(status.program_state)


class CandyTumbleErrorSensor(_TumbleSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str: return "Error"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_ERROR.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:alert-circle"

    @property
    def state(self) -> StateType:
        return self.coordinator.data.error


class CandyTumbleDelayStartSensor(_TumbleSensorBase):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str: return "Delay start"

    @property
    def unique_id(self) -> str:
        return UNIQUE_ID_TD_DELAY_START.format(self.config_id)

    @property
    def icon(self) -> str: return "mdi:clock-start"

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfTime.MINUTES

    @property
    def state(self) -> StateType:
        return self.coordinator.data.delay_start_minutes
