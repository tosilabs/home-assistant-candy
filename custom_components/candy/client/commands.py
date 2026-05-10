"""
Plaintext command builders for Candy washing machines and tumble dryers.

The plaintext format below was reverse-engineered from real captured commands
on a Candy Simply-Fi backend; verified against live API captures from
https://simply-fi.herokuapp.com/api/v1/appliances/{id}/send_command.json
"""
from typing import Optional


def washing_machine_start(
    program: int,
    temp_target: Optional[int] = None,
    temp_default: Optional[int] = None,
    spin_target: Optional[int] = None,
    spin_default: Optional[int] = None,
    steam: int = 0,
    opt_mask: int = 0,
    pause: int = 0,
    selection: int = 0,
    soil_level: Optional[int] = None,
    recipe_id: int = 0,
    check_up_state: int = 0,
) -> str:
    """
    Build a Candy washing machine START plaintext command.

    Verified format captured from Simply-Fi app:
        Perfect 20:    Write=1&Pa=0&Sel=0&PrNm=1&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
        Coloured 40:   Write=1&Pa=0&Sel=0&PrNm=2&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
        Hygiene 60:    Write=1&Pa=0&Sel=0&PrNm=3&StSt=1&SpdTgt=15&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0
        Rapid 14 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
        Rapid 30 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&SLevTgt=2&Stm=0&RecipeId=0&CheckUpState=0
        Rapid 44 min:  Write=1&Pa=0&Sel=0&PrNm=5&StSt=1&SLevTgt=3&Stm=0&RecipeId=0&CheckUpState=0
        Drain+Spin1500:Write=1&Pa=0&Sel=0&PrNm=9&StSt=1&SpdTgt=15&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0
        Drain+Spin700: Write=1&Pa=0&Sel=0&PrNm=9&StSt=1&SpdTgt=7&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0

    Notes:
        - SLevTgt  = soil/load level target (Rapid variants: 1=14min, 2=30min, 3=44min)
        - SpdTgt   = spin speed target index (x100 RPM)
        - SpdDef   = spin speed default index (x100 RPM)
        - OptMsk   = option bitmask (prewash, extra rinse, etc.) — omitted when 0
        - Stm      = steam level (0 = off)
        - TmpTgt   = user-selected temperature (omitted when None)
        - TmpDf    = program default temperature (omitted when None)
    """
    parts = [
        "Write=1",
        f"Pa={pause}",
        f"Sel={selection}",
        f"PrNm={program}",
        "StSt=1",
    ]
    if temp_target is not None:
        parts.append(f"TmpTgt={temp_target}")
    if temp_default is not None:
        parts.append(f"TmpDf={temp_default}")
    if spin_target is not None:
        parts.append(f"SpdTgt={spin_target}")
    if spin_default is not None:
        parts.append(f"SpdDef={spin_default}")
    if soil_level is not None:
        parts.append(f"SLevTgt={soil_level}")
    if opt_mask:
        parts.append(f"OptMsk={opt_mask}")
    parts.append(f"Stm={steam}")
    parts.append(f"RecipeId={recipe_id}")
    parts.append(f"CheckUpState={check_up_state}")
    return "&".join(parts)


def washing_machine_stop(program: int, delay_mode: int = 0) -> str:
    """
    Build a Candy washing machine STOP plaintext command.

    Verified format (from Simply-Fi API captures):
        Write=1&StSt=0&DelMd=0&PrNm=<N>

    The PrNm in the STOP command must match the program that was started.
    e.g. Rinse (PrNm=8) stop: Write=1&StSt=0&DelMd=0&PrNm=8
         Drain+Spin (PrNm=9) stop: Write=1&StSt=0&DelMd=0&PrNm=9
    """
    return f"Write=1&StSt=0&DelMd={delay_mode}&PrNm={program}"


def washing_machine_pause() -> str:
    """
    Build a Candy washing machine PAUSE plaintext command.
    Best-effort based on Pa= field used in start payloads.
    """
    return "Write=1&Pa=1"


def washing_machine_resume() -> str:
    """
    Build a Candy washing machine RESUME plaintext command.
    Mirrors pause with Pa=0.
    """
    return "Write=1&Pa=0"


def tumble_dryer_start(
    program: int,
    time: int = 0,
    opt_mask: int = 0,
    dry_level: int = 0,
    selection: int = 0,
    rapid: int = 0,
    pr_str: str = "",
    recipe_id: str = "0",
) -> str:
    """
    Build a Candy tumble dryer START plaintext command.

    Verified format (captured from Simply-Fi app):
        Whites:  Write=1&PrNm=1&Time=20&OptMsk=20&RecipeId=0&PrStr=Whites&StSt=1
        Eco:     Write=1&PrNm=2&Time=0&RecipeId=0&PrStr=Eco&StSt=1
        Jeans:   Write=1&PrNm=4&Time=0&RecipeId=0&PrStr=Jeans&StSt=1

    Downloadable programs additionally set Sel, DryLev, and/or Rapid when non-zero.
    OptMsk is omitted when 0 (matches observed API behaviour).
    RecipeId=0 used as local placeholder (server returns a short hash).
    """
    parts = ["Write=1", f"PrNm={program}"]
    if selection:
        parts.append(f"Sel={selection}")
    parts.append(f"Time={time}")
    if opt_mask:
        parts.append(f"OptMsk={opt_mask}")
    if dry_level:
        parts.append(f"DryLev={dry_level}")
    if rapid:
        parts.append(f"Rapid={rapid}")
    parts.append(f"RecipeId={recipe_id}")
    parts.append(f"PrStr={pr_str}")
    parts.append("StSt=1")
    return "&".join(parts)


def tumble_dryer_stop(program: int) -> str:
    """
    Build a Candy tumble dryer STOP plaintext command.

    Verified format (captured from Simply-Fi app):
        Write=1&StSt=0&PrNm=<N>
    """
    return f"Write=1&StSt=0&PrNm={program}"


def tumble_dryer_pause() -> str:
    return "Write=1&Pa=1"


def tumble_dryer_resume() -> str:
    return "Write=1&Pa=0"
