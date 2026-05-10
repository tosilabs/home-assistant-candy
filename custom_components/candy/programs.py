"""Program definitions captured from Simply-Fi backend."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class WashProgram:
    name: str
    program: int        # PrNm sent in START command
    stop_program: Optional[int] = None  # PrNm sent in STOP (if different from program)
    position: int = 0   # Sel = cloud selector position (0=base, >0=downloadable)
    temp: Optional[int] = None
    spin_target: Optional[int] = None
    spin_default: Optional[int] = None
    soil_level: Optional[int] = None   # SLevTgt (used by Rapid variants)
    steam: int = 0
    opt_mask: int = 0

    @property
    def effective_stop_program(self) -> int:
        """Return the correct PrNm to use in the STOP command."""
        return self.stop_program if self.stop_program is not None else self.program


# ---------------------------------------------------------------------------
# WASHING_MACHINE_PROGRAMS
# Verified against live Simply-Fi API captures (May 2026).
#
# Real captured START commands:
#   Perfect 20:    Write=1&Pa=0&Sel=0&PrNm=1&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
#   Coloured 40:   Write=1&Pa=0&Sel=0&PrNm=2&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
#   Hygiene 60:    Write=1&Pa=0&Sel=0&PrNm=3&StSt=1&SpdTgt=15&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0
#   Perfect Rapid: Write=1&Pa=0&Sel=0&PrNm=4&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
#   Rapid 14 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
#   Rapid 30 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&SLevTgt=2&Stm=0&RecipeId=0&CheckUpState=0
#   Rapid 44 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&SLevTgt=3&Stm=0&RecipeId=0&CheckUpState=0
#   Rinse:         Write=1&Pa=0&Sel=0&PrNm=8&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
#   Drain+Spin1500:Write=1&Pa=0&Sel=0&PrNm=9&StSt=1&SpdTgt=15&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0
#   Drain+Spin700: Write=1&Pa=0&Sel=0&PrNm=9&StSt=1&SpdTgt=7&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0
#
# Real captured STOP commands:
#   PrNm=1 stop:   Write=1&StSt=0&DelMd=0&PrNm=1
#   PrNm=3 stop:   Write=1&StSt=0&DelMd=0&PrNm=3
#   PrNm=4 stop:   Write=1&StSt=0&DelMd=0&PrNm=4
#   PrNm=5 stop:   Write=1&StSt=0&DelMd=0&PrNm=5
#   PrNm=8 stop:   Write=1&StSt=0&DelMd=0&PrNm=8
#   PrNm=9 stop:   Write=1&StSt=0&DelMd=0&PrNm=9
# ---------------------------------------------------------------------------

WASHING_MACHINE_PROGRAMS: list[WashProgram] = [
    # === Base cycles (verified from live API) ===
    WashProgram("Perfect 20", program=1),
    WashProgram("Coloured 40", program=2),
    # Hygiene 60: SpdTgt=15 & SpdDef=10 confirmed in captured command
    WashProgram("Hygiene 60", program=3, spin_target=15, spin_default=10),
    WashProgram("Perfect Rapid 59'", program=4),
    # Rapid variants: same PrNm=5, differentiated by SLevTgt (soil_level)
    # SLevTgt absent = 14 min, SLevTgt=2 = 30 min, SLevTgt=3 = 44 min
    WashProgram("Rapid 14 min", program=5),
    WashProgram("Rapid 30 min", program=5, soil_level=2),
    WashProgram("Rapid 44 min", program=5, soil_level=3),
    WashProgram("Handwash & Silk", program=6, temp=30, spin_target=8, spin_default=8),
    WashProgram("Wool", program=7, temp=40, spin_target=8, spin_default=8),
    # Rinse: PrNm=8 stop must also send PrNm=8
    WashProgram("Rinse", program=8),
    # Drain & Spin: both use PrNm=9, differentiated by SpdTgt
    WashProgram("Drain & Spin 1500", program=9, spin_target=15, spin_default=10),
    WashProgram("Drain & Spin 700",  program=9, spin_target=7,  spin_default=10),
    WashProgram("Delicates", program=10, temp=40, spin_target=4, spin_default=4, steam=1),
    WashProgram("Synthetics", program=11, temp=40, soil_level=3, spin_target=10, spin_default=10, steam=1),
    WashProgram("Cottons", program=12, temp=40, soil_level=3, spin_target=15, spin_default=15, steam=2),
    WashProgram("Whites", program=12, temp=90, soil_level=3, spin_target=14, spin_default=14, steam=2),
    WashProgram("Resistant Cottons", program=13, temp=60, soil_level=3, spin_target=15, spin_default=10, steam=2),
    WashProgram("Mixed + Easy Iron", program=14, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Smart Fi Plus", program=15, temp=60, soil_level=1, spin_target=4, spin_default=4),
    WashProgram("Silk", program=18, temp=30, spin_target=8, spin_default=8),
    WashProgram("Daily 59 min", program=19, temp=60, spin_target=15, spin_default=10),
    # === Downloadable programs from Simply-Fi cloud ===
    # — Baby —
    WashProgram("Baby Sanitizer",    program=1,  position=20, temp=60, soil_level=3, spin_target=15, spin_default=15, opt_mask=2),
    WashProgram("Cuddly Toys",       program=11, position=21, temp=40, spin_target=4, spin_default=4),
    WashProgram("Playsuits",         program=2,  position=22, temp=40, soil_level=2, spin_target=10, spin_default=10, opt_mask=16),
    # — Business —
    WashProgram("Men's Trousers",    program=9,  position=30, temp=40, spin_target=10, spin_default=10),
    WashProgram("Shirts",            program=9,  position=31, temp=30, spin_target=10, spin_default=10, opt_mask=16),
    # — Home Care —
    WashProgram("Bathrobe",          program=9,  position=40, temp=40, spin_target=10, spin_default=10, opt_mask=16),
    WashProgram("Bed Linen",         program=1,  position=41, temp=40, soil_level=2, spin_target=15, spin_default=15, opt_mask=16),
    WashProgram("Bed Linen Coloured",program=10, position=42, temp=40, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Curtains",          program=4,  position=43, temp=30, spin_target=4, spin_default=4, opt_mask=1),
    WashProgram("Curtains Coloured", program=11, position=44, temp=30, spin_target=4, spin_default=4),
    WashProgram("Delicate Tablecloths", program=2, position=45, temp=30, soil_level=1, spin_target=8, spin_default=8),
    WashProgram("Denim Jeans",       program=9,  position=46, temp=40, spin_target=10, spin_default=10),
    WashProgram("Duvet & Quilts",    program=11, position=47, temp=30, spin_target=4, spin_default=4),
    WashProgram("Mats",              program=10, position=48, temp=40, soil_level=2, spin_target=8, spin_default=8, opt_mask=1),
    WashProgram("Swimsuits & Bikinis",program=7, position=49, temp=30, spin_target=9, spin_default=9),
    WashProgram("Tablecloths",       program=1,  position=50, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Tablecloths Coloured",program=10,position=51, temp=40, soil_level=3, spin_target=10, spin_default=10),
    # — Time & Energy Saver / Rapid —
    WashProgram("Rapid Delicates 30 min", program=6,  position=60, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Refresh 14 min",    program=5,  position=61, temp=30, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Cotton", program=10, position=62, temp=40, soil_level=1, spin_target=10, spin_default=10),
    WashProgram("Time Saver Mixed",  program=2,  position=63, temp=40, soil_level=1, spin_target=10, spin_default=10),
    # — Stains —
    WashProgram("Bleaching",         program=8,  position=70, spin_target=10, spin_default=10),
    WashProgram("Blood Stains",      program=1,  position=71, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Chocolate Stains",  program=1,  position=72, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Colored Anti-Stain",program=1,  position=73, temp=40, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Fruit Stains",      program=1,  position=74, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Perfect White",     program=1,  position=75, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Stain Remover",     program=1,  position=76, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Wine Stains",       program=1,  position=77, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    # — Health & Wellness —
    WashProgram("Anti-Mites",        program=1,  position=80, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Anti-Odor",         program=1,  position=81, temp=60, soil_level=3, spin_target=10, spin_default=10, opt_mask=2),
    WashProgram("Delicate Antiallergy",program=11,position=82, temp=40, spin_target=4, spin_default=4),
    WashProgram("Masks Sanification",program=1,  position=83, temp=60, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("Masks Refresh",     program=12, position=84, temp=40, soil_level=3, spin_target=10, spin_default=10),
    WashProgram("New Clothes",       program=6,  position=85, temp=20, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Pets",              program=9,  position=86, temp=40, spin_target=10, spin_default=10),
    # — Sports —
    WashProgram("Backpacks",         program=11, position=87, temp=30, spin_target=4, spin_default=4),
    WashProgram("Diving Suits",      program=11, position=88, spin_target=4, spin_default=4),
    WashProgram("Gym Fit",           program=7,  position=89, temp=30, spin_target=10, spin_default=10),
    WashProgram("Ski Suit",          program=11, position=90, temp=30, spin_target=4, spin_default=4),
    WashProgram("Technical Fabrics", program=7,  position=91, temp=30, spin_target=10, spin_default=10),
    WashProgram("Technical Jackets", program=11, position=92, temp=30, spin_target=4, spin_default=4),
    WashProgram("Trainers",          program=11, position=93, temp=20, spin_target=4, spin_default=4),
    # — Delicate Fabrics —
    WashProgram("Cashmere",          program=3,  position=100, temp=20, spin_target=6, spin_default=6),
    WashProgram("Colored",           program=10, position=101, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Dark",              program=2,  position=102, temp=30, soil_level=2, spin_target=10, spin_default=10),
    WashProgram("Delicate Colored",  program=2,  position=103, temp=20, soil_level=1, spin_target=8, spin_default=8),
    WashProgram("Down Jackets",      program=11, position=104, temp=30, spin_target=4, spin_default=4),
    WashProgram("Lingerie",          program=7,  position=105, temp=30, spin_target=8, spin_default=8),
    WashProgram("Silk (download)",   program=3,  position=106, temp=30, spin_target=8, spin_default=8),
]

WASHING_MACHINE_PROGRAMS_BY_NAME: dict[str, WashProgram] = {
    p.name: p for p in WASHING_MACHINE_PROGRAMS
}


@dataclass(frozen=True)
class TumbleDryerProgram:
    name: str
    program: int
    time: int = 0       # max_time_level / program_time_level → Time in START command
    opt_mask: int = 0   # mask1 → OptMsk in START command (base cycles, omitted when 0)
    dry_level: int = 0  # program_drying_level → DryLev in START command (downloadable)
    selection: int = 0  # program_selection → Sel in START command (downloadable)
    rapid: int = 0      # rapid_level → Rapid in START command (downloadable)


# ---------------------------------------------------------------------------
# TUMBLE_DRYER_PROGRAMS
# Verified against live Simply-Fi API captures (May 2026).
#
# Base cycles use: Write=1&PrNm=<N>&Time=<T>&OptMsk=<M>&RecipeId=0&PrStr=<name>&StSt=1
# Downloadable programs additionally set Sel, DryLev, and/or Rapid when non-zero.
# OptMsk is omitted from command when 0 (matches observed API behaviour).
#
# program_type mapping (from API):
#   0 = Cotton sensor dry
#   1 = Cotton time dry (Duvet)
#   2 = Synthetic / wool (Woolmark, Refresh, Relax)
#   3 = Synthetic sensor dry (Jeans, Darks, Sport, downloadables)
#   4 = Time dry (Daily 45, Saving 30)
# ---------------------------------------------------------------------------

TUMBLE_DRYER_PROGRAMS: list[TumbleDryerProgram] = [
    # === Base cycles ===
    TumbleDryerProgram("Whites",            program=1,  time=20, opt_mask=20),
    TumbleDryerProgram("Eco",               program=2,  time=0),
    TumbleDryerProgram("Whites Plus",       program=3,  time=20, opt_mask=20),
    TumbleDryerProgram("Jeans",             program=4,  time=0),
    TumbleDryerProgram("Darks & Coloured",  program=5,  time=0,  opt_mask=20),
    TumbleDryerProgram("Synthetics",        program=6,  time=13, opt_mask=20),
    TumbleDryerProgram("Shirts",            program=7,  time=0,  opt_mask=20),
    TumbleDryerProgram("Woolmark",          program=8),
    TumbleDryerProgram("Daily Perfect 59'", program=9),
    TumbleDryerProgram("Daily 45 min",      program=10),
    TumbleDryerProgram("Saving 30 min",     program=11),
    TumbleDryerProgram("Refresh",           program=12),
    TumbleDryerProgram("Relax Creases",     program=13),
    TumbleDryerProgram("Sport Plus",        program=14),
    TumbleDryerProgram("Small Load",        program=15),
    # === Downloadable programs from Simply-Fi cloud ===
    # `program` = parent base cycle (PrNm), `selection`/`dry_level`/`rapid`
    # are downloadable-only parameters appended to the START command when non-zero.
    # — Home Care —
    TumbleDryerProgram("Bathrobe",              program=22, selection=2,  dry_level=4),
    TumbleDryerProgram("Bed Linen",             program=22, selection=2,  dry_level=3),
    TumbleDryerProgram("Denim Jeans",           program=23, selection=9,  dry_level=4),
    TumbleDryerProgram("Duvet",                 program=23, time=4),
    TumbleDryerProgram("Curtains",              program=24, selection=8,  dry_level=2),
    TumbleDryerProgram("Delicate Tablecloths",  program=24, selection=8,  dry_level=3),
    TumbleDryerProgram("Playsuits",             program=24, selection=8,  dry_level=3),
    TumbleDryerProgram("Cuddly Toys",           program=25, selection=12, dry_level=4),
    TumbleDryerProgram("Tablecloths",           program=27, selection=4,  dry_level=4),
    TumbleDryerProgram("Anti-Mites",            program=29, selection=12, dry_level=4),
    # — Special Care —
    TumbleDryerProgram("Baby",                  program=30, selection=4,  dry_level=3),
    TumbleDryerProgram("Easy Iron Cotton",       program=31, selection=3,  dry_level=2),
    TumbleDryerProgram("Easy Iron Synthetics",   program=31, selection=10, dry_level=2),
    TumbleDryerProgram("Gym Fit",               program=32, selection=10, dry_level=2),
    TumbleDryerProgram("Swimsuits & Bikinis",    program=32, selection=10),
    TumbleDryerProgram("Technical Fabrics",      program=32, selection=10, dry_level=2),
    TumbleDryerProgram("Backpacks",             program=33, time=7,  selection=8),
    TumbleDryerProgram("Rapid 60 min Delicates",program=34, selection=8,  rapid=2),
    TumbleDryerProgram("Lingerie",              program=24, selection=8,  dry_level=2),
    TumbleDryerProgram("Delicates Antiallergy", program=24, selection=8,  dry_level=2),
    # Renamed to avoid confusion with base cycle "Shirts"
    TumbleDryerProgram("Shirts Delicate",       program=24, selection=7,  dry_level=3),
    # — Refresh / Special —
    TumbleDryerProgram("Air Refresh",           program=35, selection=8, rapid=1),
    TumbleDryerProgram("Warm Embrace",          program=35, selection=8, rapid=1),
    TumbleDryerProgram("Dehumidifier",          program=35, selection=8, rapid=1),
    TumbleDryerProgram("Regenerates Waterproof",program=35, selection=8, rapid=1),
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
    "Smart Fi Plus": "Program inteligjent i optimizuar nga cloud Simply-Fi.",
    "Silk": "Program i butë për mëndafsh dhe materiale shumë delikate.",
    "Daily 59 min": "Program ditor i shpejtë 59 minuta.",
    "Baby Sanitizer": "Program për rroba fëmijësh me higjienizim.",
    "Cuddly Toys": "Larje e butë për lodra të buta.",
    "Playsuits": "Për kostume dhe veshje loje fëmijësh.",
    "Men's Trousers": "Program për pantallona burri, redukton rrudhat.",
    "Shirts": "Program për këmisha, redukton rrudhat.",
    "Bathrobe": "Larje e butë për roba banjoje.",
    "Bed Linen": "Për çarçafë dhe mbulesa krevati.",
    "Bed Linen Coloured": "Për çarçafë dhe mbulesa krevati me ngjyra.",
    "Curtains": "Program i butë për perde.",
    "Curtains Coloured": "Program i butë për perde me ngjyra.",
    "Delicate Tablecloths": "Për mbulesë tryeze delikate.",
    "Denim Jeans": "Program për xhinse dhe materiale denim.",
    "Duvet & Quilts": "Për jorganë dhe batanije.",
    "Mats": "Për tepihë dhe shtroja.",
    "Swimsuits & Bikinis": "Larje e butë për kostume banje.",
    "Tablecloths": "Për mbulesë tryeze.",
    "Tablecloths Coloured": "Për mbulesë tryeze me ngjyra.",
    "Rapid Delicates 30 min": "Larje e shpejtë 30 min për delikate.",
    "Refresh 14 min": "Freskim i shpejtë 14 minuta.",
    "Time Saver Cotton": "Kursim kohe për pambuk.",
    "Time Saver Mixed": "Kursim kohe për rroba të përziera.",
    "Bleaching": "Program me zbardhues për rroba të bardha.",
    "Blood Stains": "Heqja e njollave të gjakut.",
    "Chocolate Stains": "Heqja e njollave të çokollatës.",
    "Colored Anti-Stain": "Anti-njolla për rroba me ngjyra.",
    "Fruit Stains": "Heqja e njollave të frutave.",
    "Perfect White": "Program për rroba të bardha pa njolla.",
    "Stain Remover": "Heqja e njollave të ndryshme.",
    "Wine Stains": "Heqja e njollave të verës.",
    "Anti-Mites": "Program anti-marimanga/alergjenë.",
    "Anti-Odor": "Program anti-erë për rroba me erë të keqe.",
    "Delicate Antiallergy": "Program anti-alergjik për rroba delikate.",
    "Masks Sanification": "Program për higjienizim maskash.",
    "Masks Refresh": "Freskim i maskave.",
    "New Clothes": "Program i butë për rroba të reja.",
    "Pets": "Larje e rrobave me qime kafshësh.",
    "Backpacks": "Larje e çantave të shpinës.",
    "Diving Suits": "Program i butë për kombinezone zhytjeje.",
    "Gym Fit": "Larje e veshjes sportive për palestër.",
    "Ski Suit": "Program i butë për kombinezone ski.",
    "Technical Fabrics": "Për materiale teknike sportive.",
    "Technical Jackets": "Për xhaketa teknike/impermeabile.",
    "Trainers": "Larje e atleteve dhe këpucëve sportive.",
    "Cashmere": "Program shumë i butë për kashmiri.",
    "Colored": "Për rroba me ngjyra delikate.",
    "Dark": "Për rroba të errëta, ruan ngjyrën.",
    "Delicate Colored": "Për rroba me ngjyra shumë delikate.",
    "Down Jackets": "Larje e xhaketave me pupla.",
    "Lingerie": "Program shumë i butë për të brendshme.",
    "Silk (download)": "Program i butë për mëndafsh nga cloud.",
    "Perfect Rapid 59'": "Larje e plotë e shpejtë 59 minuta.",
}

TUMBLE_DRYER_PROGRAM_DESCRIPTIONS_SQ: dict[str, str] = {
    "Whites": "Tharje për rroba të bardha.",
    "Eco": "Tharje ekonomike me kursim energjie.",
    "Whites Plus": "Tharje e zgjeruar për rroba të bardha.",
    "Jeans": "Tharje për xhinse dhe materiale të trasha.",
    "Darks & Coloured": "Tharje për rroba të errëta dhe me ngjyra.",
    "Synthetics": "Tharje me nxehtësi mesatare për sintetikë.",
    "Shirts": "Tharje e butë për këmisha.",
    "Woolmark": "Tharje e kontrolluar për lesh.",
    "Daily Perfect 59'": "Program ditor rreth 59 minuta.",
    "Daily 45 min": "Program ditor 45 minuta.",
    "Saving 30 min": "Tharje e shpejtë me kursim 30 minuta.",
    "Refresh": "Freskim pa tharje të plotë.",
    "Relax Creases": "Relaksim rrudhash me avull.",
    "Sport Plus": "Për veshje sportive.",
    "Small Load": "Për ngarkesa të vogla.",
    "Bathrobe": "Për roba banjoje.",
    "Bed Linen": "Për çarçafë dhe mbulesa krevati.",
    "Denim Jeans": "Tharje e xhinse dhe denim.",
    "Duvet": "Për jorganë / batanije të trasha.",
    "Curtains": "Tharje e butë për perde.",
    "Delicate Tablecloths": "Tharje e butë për mbulesë tryeze delikate.",
    "Playsuits": "Tharje e butë për kostume loje.",
    "Cuddly Toys": "Tharje e butë për lodra të buta.",
    "Tablecloths": "Tharje e mbulesës së tryezës.",
    "Anti-Mites": "Program anti-marimanga.",
    "Baby": "Tharje e butë dhe e sigurt për veshjet e foshnjave.",
    "Easy Iron Cotton": "Tharje e pambukut për hekurosje të lehtë.",
    "Easy Iron Synthetics": "Tharje e sintetikëve për hekurosje të lehtë.",
    "Gym Fit": "Tharje e veshjes sportive.",
    "Swimsuits & Bikinis": "Tharje e butë për kostume banje.",
    "Technical Fabrics": "Tharje e materialeve teknike sportive.",
    "Backpacks": "Për çanta shpine dhe materiale të forta.",
    "Rapid 60 min Delicates": "Tharje e shpejtë 60 minuta për delikate.",
    "Lingerie": "Tharje shumë e butë për të brendshme.",
    "Delicates Antiallergy": "Tharje anti-alergjike për delikate.",
    "Shirts Delicate": "Tharje e butë për këmisha delikate.",
    "Air Refresh": "Qarkullim ajri për freskim.",
    "Warm Embrace": "Ngrohje e butë dhe freskim.",
    "Dehumidifier": "Program për ulje lagështie/freskim.",
    "Regenerates Waterproof": "Rigjenerimi i veshjes impermeabile.",
}


# ---------------------------------------------------------------------------
# WASHING_MACHINE_PROGRAM_META_SQ
# Category strings use clean names so HA dropdowns show human-readable groups.
# Sort order in the UI is controlled by sorted() in select.py.
# ---------------------------------------------------------------------------
WASHING_MACHINE_PROGRAM_META_SQ: dict[str, dict[str, str]] = {
    "Perfect 20":           {"category": "Cycles", "profile": "20°C / 1000 RPM"},
    "Coloured 40":          {"category": "Cycles", "profile": "40°C / 1000 RPM"},
    "Hygiene 60":           {"category": "Cycles", "profile": "40-60°C / 1000 RPM"},
    "Perfect Rapid 59'":    {"category": "Cycles", "profile": "40°C / 1000 RPM"},
    "Rapid 14 min":         {"category": "Cycles", "profile": "30°C / 800 RPM"},
    "Rapid 30 min":         {"category": "Cycles", "profile": "30°C / 800 RPM"},
    "Rapid 44 min":         {"category": "Cycles", "profile": "40°C / 1000 RPM"},
    "Handwash & Silk":      {"category": "Cycles", "profile": "30°C / 400 RPM"},
    "Wool":                 {"category": "Cycles", "profile": "40°C / 800 RPM"},
    "Rinse":                {"category": "Cycles", "profile": "0°C / 1000 RPM"},
    "Drain & Spin 1500":    {"category": "Cycles", "profile": "0°C / 1400-1500 RPM"},
    "Drain & Spin 700":     {"category": "Cycles", "profile": "0°C / 700 RPM"},
    "Delicates":            {"category": "Cycles", "profile": "40°C / 800 RPM"},
    "Synthetics":           {"category": "Cycles", "profile": "40°C / 1000 RPM"},
    "Cottons":              {"category": "Cycles", "profile": "60°C / 1400 RPM"},
    "Whites":               {"category": "Cycles", "profile": "90°C / 1400 RPM"},
    "Resistant Cottons":    {"category": "Cycles", "profile": "60°C / 1400 RPM"},
    "Mixed + Easy Iron":    {"category": "Cycles", "profile": "30°C / 1000 RPM"},
    "Smart Fi Plus":        {"category": "Cycles", "profile": "60°C / 400 RPM"},
    "Silk":                 {"category": "Cycles", "profile": "30°C / 800 RPM"},
    "Daily 59 min":         {"category": "Cycles", "profile": "60°C / 1000 RPM"},
    "Baby Sanitizer":       {"category": "Baby Care",         "profile": "60°C / 1000 RPM"},
    "Cuddly Toys":          {"category": "Baby Care",         "profile": "30-40°C / 400 RPM"},
    "Playsuits":            {"category": "Baby Care",         "profile": "40°C / 800 RPM"},
    "Anti-Mites":           {"category": "Health & Hygiene",  "profile": "60°C / 1000 RPM"},
    "Anti-Odor":            {"category": "Health & Hygiene",  "profile": "40-60°C / 1000 RPM"},
    "Delicate Antiallergy": {"category": "Health & Hygiene",  "profile": "40°C / 800 RPM"},
    "New Clothes":          {"category": "Health & Hygiene",  "profile": "30°C / 800 RPM"},
    "Pets":                 {"category": "Health & Hygiene",  "profile": "60°C / 1000 RPM"},
    "Masks Refresh":        {"category": "Health & Hygiene",  "profile": "40°C / 800 RPM"},
    "Masks Sanification":   {"category": "Health & Hygiene",  "profile": "60°C / 800 RPM"},
    "Bathrobe":             {"category": "Home Care",          "profile": "40°C / 800 RPM"},
    "Bed Linen":            {"category": "Home Care",          "profile": "60°C / 1000 RPM"},
    "Bed Linen Coloured":   {"category": "Home Care",          "profile": "40°C / 1000 RPM"},
    "Curtains":             {"category": "Home Care",          "profile": "30°C / 400 RPM"},
    "Curtains Coloured":    {"category": "Home Care",          "profile": "30°C / 400 RPM"},
    "Denim Jeans":          {"category": "Home Care",          "profile": "40°C / 800 RPM"},
    "Duvet & Quilts":       {"category": "Home Care",          "profile": "40°C / 800 RPM"},
    "Mats":                 {"category": "Home Care",          "profile": "40°C / 800 RPM"},
    "Swimsuits & Bikinis":  {"category": "Home Care",          "profile": "30°C / 600 RPM"},
    "Tablecloths":          {"category": "Home Care",          "profile": "60°C / 1000 RPM"},
    "Tablecloths Coloured": {"category": "Home Care",          "profile": "40°C / 1000 RPM"},
    "Delicate Tablecloths": {"category": "Home Care",          "profile": "30°C / 800 RPM"},
    "Cashmere":             {"category": "Special Care",       "profile": "20°C / 400 RPM"},
    "Colored":              {"category": "Special Care",       "profile": "30°C / 800 RPM"},
    "Dark":                 {"category": "Special Care",       "profile": "30°C / 800 RPM"},
    "Delicate Colored":     {"category": "Special Care",       "profile": "20°C / 800 RPM"},
    "Down Jackets":         {"category": "Special Care",       "profile": "30°C / 400 RPM"},
    "Lingerie":             {"category": "Special Care",       "profile": "30°C / 800 RPM"},
    "Silk (download)":      {"category": "Special Care",       "profile": "30°C / 800 RPM"},
    "Backpacks":            {"category": "Sport & Leisure",    "profile": "30°C / 400 RPM"},
    "Diving Suits":         {"category": "Sport & Leisure",    "profile": "30°C / 400 RPM"},
    "Gym Fit":              {"category": "Sport & Leisure",    "profile": "30°C / 1000 RPM"},
    "Ski Suit":             {"category": "Sport & Leisure",    "profile": "30°C / 400 RPM"},
    "Technical Fabrics":    {"category": "Sport & Leisure",    "profile": "30°C / 1000 RPM"},
    "Technical Jackets":    {"category": "Sport & Leisure",    "profile": "30°C / 400 RPM"},
    "Trainers":             {"category": "Sport & Leisure",    "profile": "20°C / 400 RPM"},
    "Bleaching":            {"category": "Stains Proof",       "profile": "0°C / 1000 RPM"},
    "Blood Stains":         {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Chocolate Stains":     {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Colored Anti-Stain":   {"category": "Stains Proof",       "profile": "40°C / 1000 RPM"},
    "Fruit Stains":         {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Perfect White":        {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Stain Remover":        {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Wine Stains":          {"category": "Stains Proof",       "profile": "60°C / 1000 RPM"},
    "Rapid Delicates 30 min": {"category": "Time & Energy Saver", "profile": "30°C / 800 RPM"},
    "Refresh 14 min":       {"category": "Time & Energy Saver", "profile": "30°C / 800 RPM"},
    "Time Saver Cotton":    {"category": "Time & Energy Saver", "profile": "40°C / 1200 RPM"},
    "Time Saver Mixed":     {"category": "Time & Energy Saver", "profile": "40°C / 1000 RPM"},
    "Shirts":               {"category": "Work",               "profile": "30°C / 1000 RPM"},
    "Men's Trousers":       {"category": "Work",               "profile": "40°C / 800 RPM"},
}


# ---------------------------------------------------------------------------
# TUMBLE_DRYER_PROGRAM_META_SQ
# ---------------------------------------------------------------------------
TUMBLE_DRYER_PROGRAM_META_SQ: dict[str, dict[str, str]] = {
    "Whites":               {"category": "Cycles",             "profile": "Nxehtësi e Lartë"},
    "Eco":                  {"category": "Cycles",             "profile": "Nxehtësi e Lartë"},
    "Whites Plus":          {"category": "Cycles",             "profile": "Nxehtësi e Lartë"},
    "Jeans":                {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Darks & Coloured":     {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Synthetics":           {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Shirts":               {"category": "Cycles",             "profile": "Nxehtësi e Ulët"},
    "Woolmark":             {"category": "Cycles",             "profile": "Nxehtësi e Ulët"},
    "Daily Perfect 59'":    {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Daily 45 min":         {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Saving 30 min":        {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Refresh":              {"category": "Cycles",             "profile": "Pa Nxehtësi"},
    "Relax Creases":        {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Sport Plus":           {"category": "Cycles",             "profile": "Nxehtësi Mesatare"},
    "Small Load":           {"category": "Cycles",             "profile": "Nxehtësi e Ulët"},
    "Baby":                 {"category": "Baby Care",          "profile": "Nxehtësi e Lartë"},
    "Cuddly Toys":          {"category": "Baby Care",          "profile": "Nxehtësi e Ulët"},
    "Delicates Antiallergy":{"category": "Health & Hygiene",   "profile": "Nxehtësi e Lartë"},
    "Air Refresh":          {"category": "Health & Hygiene",   "profile": "Pa Nxehtësi"},
    "Warm Embrace":         {"category": "Health & Hygiene",   "profile": "Pa Nxehtësi"},
    "Dehumidifier":         {"category": "Health & Hygiene",   "profile": "Pa Nxehtësi"},
    "Anti-Mites":           {"category": "Health & Hygiene",   "profile": "Nxehtësi e Lartë"},
    "Bathrobe":             {"category": "Home Care",           "profile": "Nxehtësi e Lartë"},
    "Bed Linen":            {"category": "Home Care",           "profile": "Nxehtësi e Lartë"},
    "Curtains":             {"category": "Home Care",           "profile": "Nxehtësi e Ulët"},
    "Denim Jeans":          {"category": "Home Care",           "profile": "Nxehtësi Mesatare"},
    "Duvet":                {"category": "Home Care",           "profile": "Nxehtësi e Lartë"},
    "Playsuits":            {"category": "Home Care",           "profile": "Nxehtësi e Ulët"},
    "Tablecloths":          {"category": "Home Care",           "profile": "Nxehtësi e Lartë"},
    "Delicate Tablecloths": {"category": "Home Care",           "profile": "Nxehtësi e Ulët"},
    "Regenerates Waterproof":{"category": "Special Care",      "profile": "Pa Nxehtësi"},
    "Easy Iron Cotton":     {"category": "Special Care",        "profile": "Nxehtësi Mesatare"},
    "Easy Iron Synthetics": {"category": "Special Care",        "profile": "Nxehtësi Mesatare"},
    "Lingerie":             {"category": "Special Care",        "profile": "Nxehtësi e Ulët"},
    "Shirts Delicate":      {"category": "Special Care",        "profile": "Nxehtësi e Ulët"},
    "Swimsuits & Bikinis":  {"category": "Special Care",        "profile": "Nxehtësi e Ulët"},
    "Gym Fit":              {"category": "Sport & Leisure",     "profile": "Nxehtësi Mesatare"},
    "Technical Fabrics":    {"category": "Sport & Leisure",     "profile": "Nxehtësi Mesatare"},
    "Backpacks":            {"category": "Sport & Leisure",     "profile": "Nxehtësi e Ulët"},
    "Rapid 60 min Delicates":{"category": "Time & Energy Saver","profile": "Nxehtësi Mesatare"},
}
