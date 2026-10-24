"""Keep the selected recipe and its overrides together.

The catalogue's PrNm and Sel are separate protocol fields. Never resolve a
downloadable recipe by PrNm alone: several recipes share that number.
"""
from .const import (
    DATA_KEY_WM_TEMP, DATA_KEY_WM_SPIN, DATA_KEY_WM_SOIL,
    DATA_KEY_WM_STEAM, DATA_KEY_WM_RINSE,
)
from .programs import WASHING_MACHINE_PROGRAMS_BY_NAME

PROGRAM_NAME = "wm_program_name"
RINSE_BITS = {0: 0, 1: 16, 2: 32, 3: 64}
RINSE_MASK = 16 | 32 | 64


def select_wash_program(data: dict, name: str) -> None:
    """Replace all settings atomically, including after category/restore changes."""
    program = WASHING_MACHINE_PROGRAMS_BY_NAME[name]
    rinse_bits = program.opt_mask & RINSE_MASK
    data.update({
        PROGRAM_NAME: name,
        DATA_KEY_WM_TEMP: program.temp,
        DATA_KEY_WM_SPIN: program.spin_target,
        DATA_KEY_WM_SOIL: program.soil_level,
        DATA_KEY_WM_STEAM: program.steam,
        DATA_KEY_WM_RINSE: next(
            (count for count, bit in RINSE_BITS.items() if bit == rinse_bits), 0
        ),
    })


def wash_command_parameters(data: dict) -> dict:
    """Build parameters from one recipe, preserving absent and explicit zero values."""
    program = WASHING_MACHINE_PROGRAMS_BY_NAME[data[PROGRAM_NAME]]
    mask = program.opt_mask
    rinse = data.get(DATA_KEY_WM_RINSE)
    if rinse is not None:
        mask = (mask & ~RINSE_MASK) | RINSE_BITS[rinse]
    return {
        "program": program.program,
        "selection": program.position,
        "temp_target": (program.temp if data.get(DATA_KEY_WM_TEMP) is None else data[DATA_KEY_WM_TEMP]),
        "temp_default": program.temp,
        "spin_target": (program.spin_target if data.get(DATA_KEY_WM_SPIN) is None else data[DATA_KEY_WM_SPIN]),
        "spin_default": program.spin_default,
        "soil_level": data.get(DATA_KEY_WM_SOIL, program.soil_level),
        "steam": data.get(DATA_KEY_WM_STEAM, program.steam),
        "opt_mask": mask,
    }
