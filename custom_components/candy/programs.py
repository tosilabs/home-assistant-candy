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
    opt_mask: int = 0


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
    WashProgram("Baby Sanitizer", program=1, temp=60, soil_level=3, spin_target=15, spin_default=15, opt_mask=2),
    WashProgram("Cuddly Toys", program=11, temp=40, spin_target=4, spin_default=4),
    WashProgram("Playsuits", program=2, temp=40, soil_level=2, spin_target=10, spin_default=10, opt_mask=16),
    # — Business —
    WashProgram("Men's Trousers", program=9, temp=40, spin_target=10, spin_default=10),
    WashProgram("Shirts", program=9, temp=30, spin_target=10, spin_default=10, opt_mask=16),
    # — Home Care —
    WashProgram("Bathrobe", program=9, temp=40, spin_target=10, spin_default=10, opt_mask=16),
    WashProgram("Bed Linen", program=1, temp=40, soil_level=2, spin_target=15, spin_default=15, opt_mask=16),
    WashProgram("Bed Linen Coloured", program=10, temp=40, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Curtains", program=4, temp=30, spin_target=4, spin_default=4, opt_mask=1),
    WashProgram("Curtains Coloured", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Delicate Tablecloths", program=2, temp=30, soil_level=1, spin_target=8, spin_default=8),
    WashProgram("Denim Jeans", program=9, temp=40, spin_target=10, spin_default=10),
    WashProgram("Duvet & Quilts", program=11, temp=30, spin_target=4, spin_default=4),
    WashProgram("Mats", program=10, temp=40, soil_level=2, spin_target=8, spin_default=8, opt_mask=1),
    WashProgram("Swimsuits & Bikinis", program=7, temp=30, spin_target=9, spin_default=9),
    WashProgram("Tablecloths", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Tablecloths Coloured", program=10, temp=40, soil_level=3, spin_target=10, spin_default=10),
    # — Energy Saver / Rapid —
    WashProgram("Rapid Delicates 30 min", program=6, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Refresh 14 min", program=5, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Cotton", program=10, temp=40, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Mixed", program=2, temp=40, soil_level=1, spin_target=10, spin_default=10),
    # — Stains —
    WashProgram("Bleaching", program=8, spin_target=10, spin_default=10),
    WashProgram("Blood Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Chocolate Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Colored Anti-Stain", program=1, temp=40, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Fruit Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Perfect White", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Stain Remover", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Wine Stains", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    # — Health & Wellness —
    WashProgram("Anti-Mites", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Anti-Odor", program=1, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
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


WASHING_MACHINE_PROGRAM_DESCRIPTIONS_SQ: dict[str, str] = {
    "Perfect 20": "Larje në 20°C për rroba të përditshme me konsum të ulët.",
    "Coloured 40": "Për rroba me ngjyra në 40°C.",
    "Hygiene 60": "Program higjienizues në 60°C për pastrim më të thellë.",
    "Rapid 14 min": "Larje shumë e shpejtë për rroba pak të ndotura.",
    "Rapid 30 min": "Larje e shpejtë 30 minuta.",
    "Rapid 44 min": "Larje e shpejtë 44 minuta për ngarkesë të vogël/mesatare.",
    "Handwash & Silk": "Për rroba delikate dhe mëndafsh.",
    "Wool": "Program i butë për lesh.",
    "Rinse": "Vetëm shpëlarje.",
    "Drain & Spin 1500": "Shkarkim uji dhe shtrydhje e fortë.",
    "Drain & Spin 700": "Shkarkim uji dhe shtrydhje e lehtë.",
    "Delicates": "Për rroba delikate.",
    "Synthetics": "Për materiale sintetike.",
    "Cottons": "Për pambuk dhe rroba të përditshme.",
    "Whites": "Për rroba të bardha.",
    "Resistant Cottons": "Për pambuk më të fortë / më të ndotur.",
    "Mixed + Easy Iron": "Për rroba të përziera me hekurosje më të lehtë.",
    "Baby Sanitizer": "Program për rroba fëmijësh me higjienizim.",
    "Shirts": "Program për këmisha, redukton rrudhat.",
    "Curtains": "Program i butë për perde.",
    "Anti-Mites": "Program anti-marimanga/alergjenë.",
    "Masks Sanification": "Program për higjienizim maskash.",
}

TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ: dict[str, str] = {
    "Whites": "Tharje për rroba të bardha.",
    "Eco": "Tharje ekonomike me kursim energjie.",
    "Jeans": "Tharje për xhinse dhe materiale të trasha.",
    "Shirts": "Tharje e butë për këmisha.",
    "Woolmark": "Tharje e kontrolluar për lesh.",
    "Daily Perfect 59'": "Program ditor rreth 59 minuta.",
    "Refresh": "Freskim pa tharje të plotë.",
    "Sport Plus": "Për veshje sportive.",
    "Small Load": "Për ngarkesa të vogla.",
    "Bathrobe": "Për roba banjoje.",
    "Bed Linen": "Për çarçafë dhe mbulesa krevati.",
    "Duvet": "Për jorganë / batanije të trasha.",
    "Backpacks": "Për çanta shpine dhe materiale të forta.",
    "Rapid 60 min Delicates": "Tharje e shpejtë 60 minuta për delikate.",
    "Air Refresh": "Qarkullim ajri për freskim.",
    "Dehumidifier": "Program për ulje lagështie/freskim.",
}


WASHING_MACHINE_PROGRAM_CATEGORY_SQ: dict[str, str] = {
    "Perfect 20": "Cycles",
    "Coloured 40": "Cycles",
    "Hygiene 60": "Cycles",
    "Perfect Rapid 59'": "Cycles",
    "Rapid 14 min": "Cycles",
    "Rapid 30 min": "Cycles",
    "Rapid 44 min": "Cycles",
    "Handwash & Silk": "Cycles",
    "Wool": "Cycles",
    "Rinse": "Cycles",
    "Drain & Spin 1500": "Cycles",
    "Drain & Spin 700": "Cycles",
    "Delicates": "Cycles",
    "Synthetics": "Cycles",
    "Cottons": "Cycles",
    "Whites": "Cycles",
    "Easy Iron": "Cycles",
    "Silk": "Cycles",
    "Daily 59 min": "Cycles",
    "Baby Sanitizer": "Baby Care",
    "Cuddly Toys": "Baby Care",
    "Playsuits": "Baby Care",
    "Anti-Mites": "Health & Hygiene",
    "Anti-Odor": "Health & Hygiene",
    "Delicate Antiallergy": "Health & Hygiene",
    "New Clothes": "Health & Hygiene",
    "Pets": "Health & Hygiene",
    "Masks Refresh": "Health & Hygiene",
    "Masks Sanification": "Health & Hygiene",
    "Bathrobe": "Home Care",
    "Bed Linen": "Home Care",
    "Curtains": "Home Care",
    "Denim Jeans": "Home Care",
    "Duvet & Quilts": "Home Care",
    "Mats": "Home Care",
    "Tablecloths": "Home Care",
    "Cashmere": "Special Care",
    "Dark": "Special Care",
    "Down Jackets": "Special Care",
    "Lingerie": "Special Care",
    "Backpacks": "Sport & Leisure",
    "Gym Fit": "Sport & Leisure",
    "Trainers": "Sport & Leisure",
    "Stain Remover": "Stains Proof",
    "Blood Stains": "Stains Proof",
    "Chocolate Stains": "Stains Proof",
    "Fruit Stains": "Stains Proof",
    "Wine Stains": "Stains Proof",
    "Refresh 14 min": "Time & Energy Saver",
    "Time Saver Cotton": "Time & Energy Saver",
    "Shirts": "Work",
    "Men's Trousers": "Work",
}

TUMBLE_DRYER_PROGRAM_CATEGORY_SQ: dict[str, str] = {
    "Eco": "Cycles",
    "Whites": "Cycles",
    "Jeans": "Cycles",
    "Synthetics": "Cycles",
    "Shirts": "Cycles",
    "Baby": "Baby Care",
    "Delicates Antiallergy": "Health & Hygiene",
    "Air Refresh": "Health & Hygiene",
    "Duvet": "Home Care",
    "Bed Linen": "Home Care",
    "Curtains": "Home Care",
    "Woolmark": "Special Care",
    "Lingerie": "Special Care",
    "Sport Plus": "Sport & Leisure",
    "Backpacks": "Sport & Leisure",
    "Rapid 60 min Delicates": "Time & Energy Saver",
    "Daily 45 min": "Time & Energy Saver",
    "Daily Perfect 59'": "Time & Energy Saver",
    "Relax Creases": "Time & Energy Saver",
}


WASHING_MACHINE_PROGRAM_META_SQ: dict[str, dict[str, str]] = {
    "Perfect 20": {"category": "1. Cycles", "profile": "20°C / 1000 RPM"},
    "Coloured 40": {"category": "1. Cycles", "profile": "40°C / 1000 RPM"},
    "Hygiene 60": {"category": "1. Cycles", "profile": "40-60°C / 1000 RPM"},
    "Perfect Rapid 59'": {"category": "1. Cycles", "profile": "40°C / 1000 RPM"},
    "Rapid 14 min": {"category": "1. Cycles", "profile": "30°C / 800 RPM"},
    "Rapid 30 min": {"category": "1. Cycles", "profile": "30°C / 800 RPM"},
    "Rapid 44 min": {"category": "1. Cycles", "profile": "40°C / 1000 RPM"},
    "Handwash & Silk": {"category": "1. Cycles", "profile": "30°C / 400 RPM"},
    "Wool": {"category": "1. Cycles", "profile": "40°C / 800 RPM"},
    "Rinse": {"category": "1. Cycles", "profile": "0°C / 1000 RPM"},
    "Drain & Spin 1500": {"category": "1. Cycles", "profile": "0°C / 1400-1500 RPM"},
    "Delicates": {"category": "1. Cycles", "profile": "40°C / 800 RPM"},
    "Cottons": {"category": "1. Cycles", "profile": "60°C / 1400 RPM"},
    "Whites": {"category": "1. Cycles", "profile": "90°C / 1400 RPM"},
    "Daily 59 min": {"category": "1. Cycles", "profile": "60°C / 1000 RPM"},
    "Baby Sanitizer": {"category": "2. Baby Care", "profile": "60°C / 1000 RPM"},
    "Cuddly Toys": {"category": "2. Baby Care", "profile": "30-40°C / 400 RPM"},
    "Playsuits": {"category": "2. Baby Care", "profile": "40°C / 800 RPM"},
    "Anti-Mites": {"category": "3. Health & Hygiene", "profile": "60°C / 1000 RPM"},
    "Anti-Odor": {"category": "3. Health & Hygiene", "profile": "40-60°C / 1000 RPM"},
    "Delicate Antiallergy": {"category": "3. Health & Hygiene", "profile": "40°C / 800 RPM"},
    "New Clothes": {"category": "3. Health & Hygiene", "profile": "30°C / 800 RPM"},
    "Pets": {"category": "3. Health & Hygiene", "profile": "60°C / 1000 RPM"},
    "Masks Refresh": {"category": "3. Health & Hygiene", "profile": "40°C / 800 RPM"},
    "Masks Sanification": {"category": "3. Health & Hygiene", "profile": "60°C / 800 RPM"},
    "Bathrobe": {"category": "4. Home Care", "profile": "40°C / 800 RPM"},
    "Bed Linen": {"category": "4. Home Care", "profile": "60°C / 1000 RPM"},
    "Curtains": {"category": "4. Home Care", "profile": "30°C / 400 RPM"},
    "Denim Jeans": {"category": "4. Home Care", "profile": "40°C / 800 RPM"},
    "Duvet & Quilts": {"category": "4. Home Care", "profile": "40°C / 800 RPM"},
    "Mats": {"category": "4. Home Care", "profile": "40°C / 800 RPM"},
    "Tablecloths": {"category": "4. Home Care", "profile": "60°C / 1000 RPM"},
    "Cashmere": {"category": "5. Special Care", "profile": "30°C / 400 RPM"},
    "Dark": {"category": "5. Special Care", "profile": "40°C / 800 RPM"},
    "Down Jackets": {"category": "5. Special Care", "profile": "40°C / 800 RPM"},
    "Lingerie": {"category": "5. Special Care", "profile": "30°C / 400 RPM"},
    "Backpacks": {"category": "6. Sport & Leisure", "profile": "30°C / 400 RPM"},
    "Gym Fit": {"category": "6. Sport & Leisure", "profile": "40°C / 1000 RPM"},
    "Trainers": {"category": "6. Sport & Leisure", "profile": "30°C / 600 RPM"},
    "Stain Remover": {"category": "7. Stains Proof", "profile": "40°C / 1000 RPM"},
    "Wine Stains": {"category": "7. Stains Proof", "profile": "40°C / 1000 RPM"},
    "Blood Stains": {"category": "7. Stains Proof", "profile": "40°C / 1000 RPM"},
    "Chocolate Stains": {"category": "7. Stains Proof", "profile": "40°C / 1000 RPM"},
    "Fruit Stains": {"category": "7. Stains Proof", "profile": "40°C / 1000 RPM"},
    "Refresh 14 min": {"category": "8. Time & Energy Saver", "profile": "30°C / 800 RPM"},
    "Time Saver Cotton": {"category": "8. Time & Energy Saver", "profile": "40°C / 1200 RPM"},
    "Shirts": {"category": "9. Work", "profile": "40°C / 600 RPM"},
    "Men's Trousers": {"category": "9. Work", "profile": "40°C / 800 RPM"},
}

TUMBLE_DRYER_PROGRAM_META_SQ: dict[str, dict[str, str]] = {
    "Eco": {"category": "1. Cycles", "profile": "Nxehtësi e Lartë"},
    "Whites": {"category": "1. Cycles", "profile": "Nxehtësi e Lartë"},
    "Jeans": {"category": "1. Cycles", "profile": "Nxehtësi Mesatare"},
    "Synthetics": {"category": "1. Cycles", "profile": "Nxehtësi Mesatare"},
    "Shirts": {"category": "1. Cycles", "profile": "Nxehtësi e Ulët"},
    "Baby": {"category": "2. Baby Care", "profile": "Nxehtësi e Lartë"},
    "Delicates Antiallergy": {"category": "3. Health & Hygiene", "profile": "Nxehtësi e Lartë"},
    "Air Refresh": {"category": "3. Health & Hygiene", "profile": "Pa Nxehtësi"},
    "Duvet": {"category": "4. Home Care", "profile": "Nxehtësi e Lartë"},
    "Bed Linen": {"category": "4. Home Care", "profile": "Nxehtësi e Lartë"},
    "Curtains": {"category": "4. Home Care", "profile": "Nxehtësi e Ulët"},
    "Woolmark": {"category": "5. Special Care", "profile": "Nxehtësi e Ulët"},
    "Lingerie": {"category": "5. Special Care", "profile": "Nxehtësi e Ulët"},
    "Sport Plus": {"category": "6. Sport & Leisure", "profile": "Nxehtësi Mesatare"},
    "Backpacks": {"category": "6. Sport & Leisure", "profile": "Nxehtësi e Ulët"},
    "Rapid 60 min Delicates": {"category": "7. Time & Energy Saver", "profile": "Nxehtësi Mesatare"},
    "Daily 45 min": {"category": "7. Time & Energy Saver", "profile": "Nxehtësi Mesatare"},
    "Daily Perfect 59'": {"category": "7. Time & Energy Saver", "profile": "Nxehtësi Mesatare"},
    "Relax Creases": {"category": "7. Time & Energy Saver", "profile": "Nxehtësi Mesatare"},
}
