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
    # === Base cycles (selector_position 1–19 from appliance backend) ===
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
    WashProgram("Whites", program=12, temp=90, soil_level=3, spin_target=14, spin_default=14, steam=2),
    WashProgram("Resistant Cottons", program=13, temp=60, soil_level=3, spin_target=15, spin_default=10, steam=2),
    WashProgram("Mixed + Easy Iron", program=14, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Smart Fi Plus", program=15, temp=90, soil_level=1, spin_target=4, spin_default=4),
    WashProgram("Silk", program=18, temp=30),
    WashProgram("Daily 59 min", program=19, temp=60, spin_target=15, spin_default=10),
    # === Downloadable programs from Simply-Fi cloud (wm_wd_programs.json) ===
    # Each runs on the parent base cycle (`program` below) with these defaults.
    # — Baby —
    WashProgram("Baby Sanitizer", program=1, temp=60, soil_level=3, spin_target=15, spin_default=15),
    WashProgram("Cuddly Toys", program=11, temp=40, spin_target=4, spin_default=4),
    WashProgram("Playsuits", program=2, temp=40, soil_level=2, spin_target=10, spin_default=10),
    # — Business —
    WashProgram("Men's Trousers", program=9, temp=40, spin_target=10, spin_default=10),
    WashProgram("Shirts", program=9, temp=30, spin_target=10, spin_default=10),
    # — Home Care —
    WashProgram("Bathrobe", program=9, temp=40, spin_target=10, spin_default=10),
    WashProgram("Bed Linen", program=1, temp=40, soil_level=2, spin_target=15, spin_default=15),
    WashProgram("Bed Linen Coloured", program=10, temp=40, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Curtains", program=4, temp=30, spin_target=4, spin_default=4),
    WashProgram("Curtains Coloured", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Delicate Tablecloths", program=2, temp=30, soil_level=1, spin_target=8, spin_default=8),
    WashProgram("Denim Jeans", program=9, temp=40, spin_target=10, spin_default=10),
    WashProgram("Duvet & Quilts", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Mats", program=10, temp=40, soil_level=2, spin_target=8, spin_default=8),
    WashProgram("Swimsuits & Bikinis", program=7, temp=30, spin_target=9, spin_default=9),
    WashProgram("Tablecloths", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Tablecloths Coloured", program=10, temp=40, soil_level=3, spin_target=10, spin_default=10),
    # — Energy Saver / Rapid —
    WashProgram("Rapid Delicates 30 min", program=6, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Refresh 14 min", program=5, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Cotton", program=10, temp=40, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Mixed", program=2, temp=40, soil_level=1, spin_target=10, spin_default=10),
    # — Stains —
    WashProgram("Bleaching", program=8, spin_target=10, spin_default=10),
    WashProgram("Blood Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Chocolate Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Colored Anti-Stain", program=1, temp=40, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Fruit Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Perfect White", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Stain Remover", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Wine Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    # — Health & Wellness —
    WashProgram("Anti-Mites", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Anti-Odor", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Delicate Antiallergy", program=11, temp=40, spin_target=4, spin_default=4),
    WashProgram("Masks Sanification", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Masks Refresh", program=12, temp=40, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("New Clothes", program=6, temp=20, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Pets", program=9, temp=40, spin_target=10, spin_default=10),
    # — Sports —
    WashProgram("Backpacks", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Diving Suits", program=11, spin_target=4, spin_default=4),
    WashProgram("Gym Fit", program=7, temp=30, spin_target=10, spin_default=10),
    WashProgram("Ski Suit", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Technical Fabrics", program=7, temp=30, spin_target=10, spin_default=10),
    WashProgram("Technical Jackets", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Trainers", program=11, temp=20, spin_target=4, spin_default=4),
    # — Delicate Fabrics —
    WashProgram("Cashmere", program=3, temp=20, spin_target=6, spin_default=6),
    WashProgram("Colored", program=10, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Dark", program=2, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Delicate Colored", program=2, temp=20, soil_level=1, spin_target=8, spin_default=8),
    WashProgram("Down Jackets", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Lingerie", program=7, temp=30, spin_target=8, spin_default=8),
    WashProgram("Silk (download)", program=3, temp=30, spin_target=8, spin_default=8),
]

WASHING_MACHINE_PROGRAMS_BY_NAME: dict[str, WashProgram] = {
    p.name: p for p in WASHING_MACHINE_PROGRAMS
}


@dataclass(frozen=True)
class TumbleDryerProgram:
    name: str
    program: int
    time: int = 0       # max_time_level / program_time_level → Time in START command
    opt_mask: int = 0   # mask1 → OptMsk in START command (base cycles)
    dry_level: int = 0  # program_drying_level → DryLev in START command (downloadable)
    selection: int = 0  # program_selection → Sel in START command (downloadable)
    rapid: int = 0      # rapid_level → Rapid in START command (downloadable)


TUMBLE_DRYER_PROGRAMS: list[TumbleDryerProgram] = [
    # === Base cycles (selector_position 1–15 from appliance backend) ===
    TumbleDryerProgram("Whites", program=1, time=20, opt_mask=20),
    TumbleDryerProgram("Eco", program=2, time=0, opt_mask=0),
    TumbleDryerProgram("Whites Plus", program=3, time=20, opt_mask=20),
    TumbleDryerProgram("Jeans", program=4, time=0, opt_mask=0),
    TumbleDryerProgram("Darks & Coloured", program=5, time=0, opt_mask=20),
    TumbleDryerProgram("Synthetics", program=6, time=13, opt_mask=20),
    TumbleDryerProgram("Shirts", program=7, time=0, opt_mask=20),
    TumbleDryerProgram("Woolmark", program=8),
    TumbleDryerProgram("Daily Perfect 59'", program=9),
    TumbleDryerProgram("Daily 45 min", program=10),
    TumbleDryerProgram("Saving 30 min", program=11),
    TumbleDryerProgram("Refresh", program=12),
    TumbleDryerProgram("Relax Creases", program=13),
    TumbleDryerProgram("Sport Plus", program=14),
    TumbleDryerProgram("Small Load", program=15),
    # === Downloadable programs from Simply-Fi cloud (td_wifi_download_program) ===
    # `program` = parent base cycle (PrNm), `selection`/`dry_level`/`rapid` are
    # downloadable-only parameters appended to the START command when non-zero.
    # — Home Care —
    TumbleDryerProgram("Bathrobe", program=22, selection=2, dry_level=4),
    TumbleDryerProgram("Bed Linen", program=22, selection=2, dry_level=3),
    TumbleDryerProgram("Denim Jeans", program=23, selection=9, dry_level=4),
    TumbleDryerProgram("Duvet", program=23, time=4),
    TumbleDryerProgram("Curtains", program=24, selection=8, dry_level=2),
    TumbleDryerProgram("Delicate Tablecloths", program=24, selection=8, dry_level=3),
    TumbleDryerProgram("Playsuits", program=24, selection=8, dry_level=3),
    TumbleDryerProgram("Cuddly Toys", program=25, selection=12, dry_level=4),
    TumbleDryerProgram("Tablecloths", program=27, selection=4, dry_level=4),
    TumbleDryerProgram("Anti-Mites", program=29, selection=12, dry_level=4),
    # — Special Care —
    TumbleDryerProgram("Baby", program=30, selection=4, dry_level=3),
    TumbleDryerProgram("Easy Iron Cotton", program=31, selection=3, dry_level=2),
    TumbleDryerProgram("Easy Iron Synthetics", program=31, selection=10, dry_level=2),
    TumbleDryerProgram("Gym Fit", program=32, selection=10, dry_level=2),
    TumbleDryerProgram("Swimsuits & Bikinis", program=32, selection=10),
    TumbleDryerProgram("Technical Fabrics", program=32, selection=10, dry_level=2),
    TumbleDryerProgram("Backpacks", program=33, time=7, selection=8),
    TumbleDryerProgram("Rapid 60 min Delicates", program=34, selection=8, rapid=2),
    TumbleDryerProgram("Lingerie", program=24, selection=8, dry_level=2),
    TumbleDryerProgram("Delicates Antiallergy", program=24, selection=8, dry_level=2),
    TumbleDryerProgram("Shirts (download)", program=24, selection=7, dry_level=3),
    # — Refresh / Special —
    TumbleDryerProgram("Air Refresh", program=35, selection=8, rapid=1),
    TumbleDryerProgram("Warm Embrace", program=35, selection=8, rapid=1),
    TumbleDryerProgram("Dehumidifier", program=35, selection=8, rapid=1),
    TumbleDryerProgram("Regenerates Waterproof", program=35, selection=8, rapid=1),
]

TUMBLE_DRYER_PROGRAMS_BY_NAME: dict[str, TumbleDryerProgram] = {
    p.name: p for p in TUMBLE_DRYER_PROGRAMS
}
