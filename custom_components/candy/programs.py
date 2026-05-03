"""Washing machine program definitions captured from Simply-Fi app."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WashProgram:
    name: str
    program: int
    spin_target: Optional[int] = None
    spin_default: Optional[int] = None
    soil_level: Optional[int] = None
    steam: int = 0


WASHING_MACHINE_PROGRAMS: list[WashProgram] = [
    WashProgram("Perfect 20", program=1),
    WashProgram("Coloured 40", program=2),
    WashProgram("Hygiene 60", program=3, spin_target=15, spin_default=10),
    WashProgram("Perfect Rapid 59'", program=4),
    WashProgram("Rapid 14 min", program=5),
    WashProgram("Rapid 30 min", program=5, soil_level=2),
    WashProgram("Rapid 44 min", program=5, soil_level=3),
    WashProgram("Rinse", program=8),
    WashProgram("Drain & Spin 1500", program=9, spin_target=15, spin_default=10),
    WashProgram("Drain & Spin 700", program=9, spin_target=7, spin_default=10),
]

WASHING_MACHINE_PROGRAMS_BY_NAME: dict[str, WashProgram] = {
    p.name: p for p in WASHING_MACHINE_PROGRAMS
}
