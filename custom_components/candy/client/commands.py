"""
Plaintext command builders for Candy washing machines.

The plaintext format below was reverse-engineered from real captured commands
on a Candy washing machine; it may not apply unchanged to dishwashers, dryers
or ovens. The integration's `send_plaintext_command` and `send_raw_command`
services let advanced users override anything that doesn't fit their model.
"""
from typing import Optional


def washing_machine_start(
    program: int,
    temp: Optional[int] = None,
    spin_target: Optional[int] = None,
    spin_default: Optional[int] = None,
    soil_level: Optional[int] = None,
    steam: int = 0,
    pause: int = 0,
    selection: int = 0,
    recipe_id: int = 0,
    check_up_state: int = 0,
) -> str:
    """
    Build a Candy washing machine START plaintext command.

    The minimal verified format is:
        Write=1&Pa=0&Sel=0&PrNm=<N>&StSt=1&Stm=0&RecipeId=0&CheckUpState=0
    Optional fields (Temp, SLevTgt, SpdTgt, SpdDef) are appended only when set,
    matching the patterns observed in captured commands.
    """
    parts = [
        f"Write=1",
        f"Pa={pause}",
        f"Sel={selection}",
        f"PrNm={program}",
        f"StSt=1",
    ]
    if temp is not None:
        parts.append(f"Temp={temp}")
    if soil_level is not None:
        parts.append(f"SLevTgt={soil_level}")
    if spin_target is not None:
        parts.append(f"SpdTgt={spin_target}")
    if spin_default is not None:
        parts.append(f"SpdDef={spin_default}")
    parts.append(f"Stm={steam}")
    parts.append(f"RecipeId={recipe_id}")
    parts.append(f"CheckUpState={check_up_state}")
    return "&".join(parts)


def washing_machine_stop(program: int, delay_mode: int = 0) -> str:
    """
    Build a Candy washing machine STOP plaintext command.

    Verified format:
        Write=1&StSt=0&DelMd=0&PrNm=<N>
    """
    return f"Write=1&StSt=0&DelMd={delay_mode}&PrNm={program}"


def washing_machine_pause() -> str:
    """
    Build a Candy washing machine PAUSE plaintext command.
    Best-effort guess based on the `Pa=` field used in start payloads.
    """
    return "Write=1&Pa=1"


def washing_machine_resume() -> str:
    """
    Build a Candy washing machine RESUME plaintext command.
    Best-effort guess; mirrors pause with Pa=0.
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

    Verified format (captured from Simply-Fi app, Whites program):
        Write=1&PrNm=1&Time=20&OptMsk=20&RecipeId=2ciC2s&PrStr=Whites&StSt=1
    RecipeId is a server-generated short hash; "0" is used as a local placeholder.
    Time = max_time_level/program_time_level, OptMsk = mask1 (base cycles).
    Downloadable programs additionally use Sel, DryLev, and/or Rapid when non-zero.
    """
    parts = [f"Write=1", f"PrNm={program}"]
    if selection:
        parts.append(f"Sel={selection}")
    parts.append(f"Time={time}")
    parts.append(f"OptMsk={opt_mask}")
    if dry_level:
        parts.append(f"DryLev={dry_level}")
    if rapid:
        parts.append(f"Rapid={rapid}")
    parts.append(f"RecipeId={recipe_id}")
    parts.append(f"PrStr={pr_str}")
    parts.append(f"StSt=1")
    return "&".join(parts)


def tumble_dryer_stop(program: int) -> str:
    """
    Build a Candy tumble dryer STOP plaintext command.

    Verified format (captured from Simply-Fi app):
        Write=1&StSt=0&PrNm=1
    """
    return f"Write=1&StSt=0&PrNm={program}"


def tumble_dryer_pause() -> str:
    return "Write=1&Pa=1"


def tumble_dryer_resume() -> str:
    return "Write=1&Pa=0"
