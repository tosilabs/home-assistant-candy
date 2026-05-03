"""Program definitions captured from Simply-Fi backend."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WashProgram:
    name: str
    program: int
    temp: Optional[int] = None
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
    WashProgram("Handwash & Silk", program=6, temp=30, spin_target=8, spin_default=8),
    WashProgram("Wool", program=7, temp=40, spin_target=8, spin_default=8),
    WashProgram("Rinse", program=8),
    WashProgram("Drain & Spin 1500", program=9, spin_target=15, spin_default=10),
    WashProgram("Drain & Spin 700", program=9, spin_target=7, spin_default=10),
    WashProgram("Delicates", program=10, temp=40, spin_target=4, spin_default=4, steam=1),
    WashProgram("Synthetics", program=11, temp=40, soil_level=3, spin_target=10, spin_default=10, steam=1),
    WashProgram("Cottons", program=12, temp=40, soil_level=3, spin_target=15, spin_default=15, steam=2),
    WashProgram("Resistant Cottons", program=13, temp=60, soil_level=3, spin_target=15, spin_default=10, steam=2),
    WashProgram("Mixed + Easy Iron", program=14, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Smart Fi Plus", program=15, temp=90, soil_level=1, spin_target=4, spin_default=4),
    WashProgram("Silk", program=18, temp=30),
    WashProgram("Daily 59 min", program=19, temp=60, spin_target=15, spin_default=10),
]

WASHING_MACHINE_PROGRAMS_BY_NAME: dict[str, WashProgram] = {
    p.name: p for p in WASHING_MACHINE_PROGRAMS
}


@dataclass(frozen=True)
class TumbleDryerProgram:
    name: str
    program: int
    dry_level: Optional[int] = None
    dry_level_target: Optional[int] = None


TUMBLE_DRYER_PROGRAMS: list[TumbleDryerProgram] = [
    TumbleDryerProgram("Whites", program=1, dry_level=2),
    TumbleDryerProgram("Eco", program=2, dry_level=2),
    TumbleDryerProgram("Whites Plus", program=3, dry_level=2),
    TumbleDryerProgram("Jeans", program=4, dry_level=4),
    TumbleDryerProgram("Darks & Coloured", program=5, dry_level=2),
    TumbleDryerProgram("Synthetics", program=6, dry_level=2),
    TumbleDryerProgram("Shirts", program=7, dry_level=2),
    TumbleDryerProgram("Woolmark", program=8),
    TumbleDryerProgram("Daily Perfect 59'", program=9, dry_level=2),
    TumbleDryerProgram("Daily 45 min", program=10),
    TumbleDryerProgram("Saving 30 min", program=11),
    TumbleDryerProgram("Refresh", program=12),
    TumbleDryerProgram("Relax Creases", program=13),
    TumbleDryerProgram("Sport Plus", program=14, dry_level=3),
    TumbleDryerProgram("Small Load", program=15, dry_level=3),
]

TUMBLE_DRYER_PROGRAMS_BY_NAME: dict[str, TumbleDryerProgram] = {
    p.name: p for p in TUMBLE_DRYER_PROGRAMS
}
