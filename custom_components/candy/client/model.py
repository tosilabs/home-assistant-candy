from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StatusCode(Enum):
    def __init__(self, code: int, label: str):
        self.code = code
        self.label = label

    def __str__(self):
        return self.label

    @classmethod
    def from_code(cls, code: int):
        for state in cls:
            if code == state.code:
                return state
        raise ValueError(f"Unrecognized code when parsing {cls}: {code}")


class MachineState(StatusCode):
    IDLE = (1, "Ready")
    RUNNING = (2, "Running")
    PAUSED = (3, "Paused")
    DELAYED_START_SELECTION = (4, "Delayed start selection")
    DELAYED_START_PROGRAMMED = (5, "Delayed start programmed")
    ERROR = (6, "Error")
    FINISHED1 = (7, "Finished")
    FINISHED2 = (8, "Finished")


class WashProgramState(StatusCode):
    STOPPED = (0, "Ready")
    PRE_WASH = (1, "Pre-wash")
    WASH = (2, "Wash")
    RINSE = (3, "Rinse")
    LAST_RINSE = (4, "Last rinse")
    END = (5, "End")
    DRYING = (6, "Drying")
    ERROR = (7, "Error")
    STEAM = (8, "Steam")
    GOOD_NIGHT = (9, "Spin - Good Night")  # TODO: GN pause?
    SPIN = (10, "Spin")


class WashProgramType(StatusCode):
    EXTRA_CARE = (1, "Extra Care")
    AIO_59 = (2, "All In One 59'")
    RAPID_143044 = (3, "Rapid Care 14'/30'/44'")
    ALLERGY_CARE = (4, "Allergy Care 60°C")
    FRESH_CARE = (5, "Fresh Care")
    SOFT_CARE = (6, "Soft Care")
    FITNESS_CARE = (7, "Fitness Care")
    RINSE_PR = (8, "Rinse")
    DRAIN_SPIN = (9, "Drain & Spin")
    MIXED = (10, "Mixed")
    ECO20 = (11, "Eco 20°C")
    WOOL_HAND = (12, "Wool & Handwash")
    ECO_4060 = (13, "Eco 40°C-60°C")
    COTTONS = (14, "Cottons")
    ONE_FI = (15, "One Fi Extra")


@dataclass
class WashingMachineStatus:
    machine_state: MachineState
    program_state: WashProgramState
    program_type: WashProgramType
    program: Optional[int]
    program_code: Optional[int]
    temp: int
    spin_speed: int
    remaining_minutes: int
    remote_control: bool
    fill_percent: Optional[int]  # 0...100
    error: int = 0
    soil_level: int = 0   # 0=none 1=light 2=medium 3=heavy
    steam: int = 0        # 0=off 1=low 2=high

    @classmethod
    def from_json(cls, json):
        return cls(
            machine_state=MachineState.from_code(int(json["MachMd"])),
            program_state=WashProgramState.from_code(int(json["PrPh"])),
            program_type=WashProgramType.from_code(int(json["Pr"])),
            program=int(json["PrNm"]) if "PrNm" in json else None,
            program_code=int(json["PrCode"]) if "PrCode" in json else None,
            temp=int(json["Temp"]),
            spin_speed=int(json["SpinSp"]) * 100,
            remaining_minutes=int(json["RemTime"]),
            remote_control=json["WiFiStatus"] == "1",
            fill_percent=int(json["FillR"]) if "FillR" in json else None,
            error=int(json.get("Err", 0)),
            soil_level=int(json.get("SLevel", 0)),
            steam=int(json.get("Steam", 0)),
        )


class DryerProgramState(StatusCode):
    STOPPED = (0, "Ready")
    RUNNING = (2, "Running")
    END = (3, "End")


class DryerCycleState(StatusCode):
    LEVEL_NONE = (0, "No dry")
    LEVEL_IRON = (1, "Iron dry")
    LEVEL_HANG = (2, "Ready to wear")
    LEVEL_STORE = (3, "Cupboard dry")
    LEVEL_BONE = (4, "Bone dry")


@dataclass
class TumbleDryerStatus:
    machine_state: MachineState
    program_state: DryerProgramState
    cycle_state: DryerCycleState
    program: int
    remaining_minutes: int
    remote_control: bool
    dry_level: int
    dry_level_selected: int
    refresh: bool
    need_clean_filter: bool
    water_tank_full: bool
    door_closed: bool
    error: int = 0

    @classmethod
    def from_json(cls, json):
        return cls(
            machine_state=MachineState.from_code(int(json["StatoTD"])),
            program_state=DryerProgramState.from_code(int(json["PrPh"])),
            cycle_state=DryerCycleState.from_code(int(json["DryLev"])),
            program=int(json["Pr"]),
            remaining_minutes=int(json["RemTime"]),
            remote_control=json["StatoWiFi"] == "1",
            dry_level=int(json["DryLev"]),
            dry_level_selected=int(json["DryingManagerLevel"]),
            refresh=json["Refresh"] == "1",
            need_clean_filter=json["CleanFilter"] == "1",
            water_tank_full=json["WaterTankFull"] == "1",
            door_closed=json["DoorState"] == "1",
            error=int(json.get("CodiceErrore", 0)),
        )


class DishwasherState(StatusCode):
    """
    Dishwashers have a single state combining the machine state and program state
    """

    IDLE = (0, "Idle")
    PRE_WASH = (1, "Pre-wash")
    WASH = (2, "Wash")
    RINSE = (3, "Rinse")
    DRYING = (4, "Drying")
    FINISHED = (5, "Finished")


@dataclass
class DishwasherStatus:
    machine_state: DishwasherState
    program: str
    remaining_minutes: int
    delayed_start_hours: Optional[int]
    door_open: bool
    door_open_allowed: Optional[bool]
    eco_mode: bool
    remote_control: bool
    salt_empty: bool
    rinse_aid_empty: bool

    @classmethod
    def from_json(cls, json):
        return cls(
            machine_state=DishwasherState.from_code(int(json["StatoDWash"])),
            program=DishwasherStatus.parse_program(json),
            remaining_minutes=int(json["RemTime"]),
            delayed_start_hours=int(json["DelayStart"]) if json["DelayStart"] != "0" else None,
            door_open=json["OpenDoor"] != "0",
            door_open_allowed=json["OpenDoorOpt"] == "1" if "OpenDoorOpt" in json else None,
            eco_mode=json["Eco"] != "0",
            remote_control=json["StatoWiFi"] == "1",
            salt_empty=json["MissSalt"] == "1",
            rinse_aid_empty=json["MissRinse"] == "1"
        )

    @staticmethod
    def parse_program(json) -> str:
        """
        Parse final program label, like P1, P1+, P1-
        """
        program = json["Program"]
        # Some dishwashers don't include the OpzProg field
        option = json.get("OpzProg")
        if option == "p":
            return program + "+"
        elif option == "m":
            return program + "-"
        else:
            # Third OpzProg value is 0
            return program


class OvenState(StatusCode):
    IDLE = (0, "Idle")
    HEATING = (1, "Heating")


@dataclass
class OvenStatus:
    machine_state: OvenState
    program: int
    selection: int
    temp: float
    temp_reached: bool
    program_length_minutes: Optional[int]
    remote_control: bool

    @classmethod
    def from_json(cls, json):
        return cls(
            machine_state=OvenState.from_code(int(json["StartStop"])),
            program=int(json["Program"]),
            selection=int(json["Selettore"]),
            temp=round(fahrenheit_to_celsius(int(json["TempRead"]))),
            temp_reached=json["TempSetRaggiunta"] == "1",
            program_length_minutes=int(json["TimeProgr"]) if "TimeProgr" in json else None,
            remote_control=json["StatoWiFi"] == "1",
        )


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5.0 / 9.0
