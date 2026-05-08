from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Values the Candy API uses to signal "not applicable" or "unknown"
SENTINEL = 255


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

    @classmethod
    def from_code_safe(cls, code: int):
        """Return None instead of raising when code is unrecognised or sentinel."""
        if code == SENTINEL:
            return None
        try:
            return cls.from_code(code)
        except ValueError:
            return None


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
    GOOD_NIGHT = (9, "Spin - Good Night")
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


def _sentinel_to_none(value: int) -> Optional[int]:
    """Return None if value is the Candy sentinel (255), else return value."""
    return None if value == SENTINEL else value


@dataclass
class WashingMachineStatus:
    machine_state: MachineState
    program_state: WashProgramState
    program_type: Optional[WashProgramType]   # None when program code is 255 / unknown
    program: Optional[int]
    program_code: Optional[int]
    temp: Optional[int]          # None when sentinel
    spin_speed: Optional[int]    # None when sentinel (stored as rpm = raw * 100)
    remaining_minutes: int
    remote_control: bool
    fill_percent: Optional[int]
    error: Optional[int]         # None means no error / sentinel
    soil_level: Optional[int]    # None when sentinel
    steam: int
    delay_start_minutes: Optional[int]  # None = not programmed

    @classmethod
    def from_json(cls, json: dict):
        raw_err = int(json.get("Err", 0))
        raw_spin = int(json.get("SpinSp", 0))
        raw_temp = int(json.get("Temp", 0))
        raw_soil = int(json.get("SLevel", 0))
        raw_delay = int(json.get("DelVal", 0))
        raw_pr = int(json.get("Pr", 0))

        return cls(
            machine_state=MachineState.from_code(int(json["MachMd"])),
            program_state=WashProgramState.from_code(int(json["PrPh"])),
            program_type=WashProgramType.from_code_safe(raw_pr),
            program=int(json["PrNm"]) if "PrNm" in json else None,
            program_code=int(json["PrCode"]) if "PrCode" in json else None,
            temp=_sentinel_to_none(raw_temp),
            spin_speed=None if _sentinel_to_none(raw_spin) is None else _sentinel_to_none(raw_spin) * 100,
            remaining_minutes=int(json.get("RemTime", 0)),
            remote_control=json.get("WiFiStatus") == "1",
            fill_percent=int(json["FillR"]) if "FillR" in json else None,
            error=_sentinel_to_none(raw_err) if raw_err != 0 else None,
            soil_level=_sentinel_to_none(raw_soil),
            steam=int(json.get("Steam", 0)),
            delay_start_minutes=_sentinel_to_none(raw_delay),
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
    cycle_state: Optional[DryerCycleState]  # None when sentinel
    program: int
    remaining_minutes: int
    remote_control: bool
    dry_level: Optional[int]           # None when sentinel
    dry_level_selected: Optional[int]  # None when sentinel
    refresh: bool
    need_clean_filter: bool
    water_tank_full: bool
    door_closed: bool
    error: Optional[int]               # None = no error
    delay_start_minutes: Optional[int] # None = not programmed

    @classmethod
    def from_json(cls, json: dict):
        raw_err = int(json.get("CodiceErrore", 0))
        raw_dry_lev = int(json.get("DryLev", 0))
        raw_dry_sel = int(json.get("DryingManagerLevel", 0))
        raw_delay = int(json.get("DelVal", 0))

        return cls(
            machine_state=MachineState.from_code(int(json["StatoTD"])),
            program_state=DryerProgramState.from_code(int(json["PrPh"])),
            cycle_state=DryerCycleState.from_code_safe(raw_dry_lev),
            program=int(json.get("Pr", 0)),
            remaining_minutes=int(json.get("RemTime", 0)),
            remote_control=json.get("StatoWiFi") == "1",
            dry_level=_sentinel_to_none(raw_dry_lev),
            dry_level_selected=_sentinel_to_none(raw_dry_sel),
            refresh=json.get("Refresh") == "1",
            need_clean_filter=json.get("CleanFilter") == "1",
            water_tank_full=json.get("WaterTankFull") == "1",
            door_closed=json.get("DoorState") == "1",
            error=_sentinel_to_none(raw_err) if raw_err != 0 else None,
            delay_start_minutes=_sentinel_to_none(raw_delay),
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
    def from_json(cls, json: dict):
        return cls(
            machine_state=DishwasherState.from_code(int(json["StatoDWash"])),
            program=DishwasherStatus.parse_program(json),
            remaining_minutes=int(json.get("RemTime", 0)),
            delayed_start_hours=int(json["DelayStart"]) if json.get("DelayStart", "0") != "0" else None,
            door_open=json.get("OpenDoor", "0") != "0",
            door_open_allowed=json["OpenDoorOpt"] == "1" if "OpenDoorOpt" in json else None,
            eco_mode=json.get("Eco", "0") != "0",
            remote_control=json.get("StatoWiFi") == "1",
            salt_empty=json.get("MissSalt") == "1",
            rinse_aid_empty=json.get("MissRinse") == "1",
        )

    @staticmethod
    def parse_program(json) -> str:
        """
        Parse final program label, like P1, P1+, P1-
        """
        program = json.get("Program", "?")
        option = json.get("OpzProg")
        if option == "p":
            return program + "+"
        elif option == "m":
            return program + "-"
        else:
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
    def from_json(cls, json: dict):
        return cls(
            machine_state=OvenState.from_code(int(json["StartStop"])),
            program=int(json.get("Program", 0)),
            selection=int(json.get("Selettore", 0)),
            temp=round(fahrenheit_to_celsius(int(json["TempRead"]))),
            temp_reached=json.get("TempSetRaggiunta") == "1",
            program_length_minutes=int(json["TimeProgr"]) if "TimeProgr" in json else None,
            remote_control=json.get("StatoWiFi") == "1",
        )


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5.0 / 9.0
