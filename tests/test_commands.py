"""Tests for plaintext command builders."""
from custom_components.candy.client.commands import (washing_machine_pause,
                                                     washing_machine_resume,
                                                     washing_machine_start,
                                                     washing_machine_stop)


def test_wm_start_minimal():
    assert washing_machine_start(program=4) == (
        "Write=1&Pa=0&Sel=0&PrNm=4&StSt=1&Stm=0&RecipeId=0&CheckUpState=0"
    )


def test_wm_start_with_options():
    assert washing_machine_start(
        program=13, spin_target=15, spin_default=10
    ) == (
        "Write=1&Pa=0&Sel=0&PrNm=13&StSt=1&SpdTgt=15&SpdDef=10&Stm=0&RecipeId=0&CheckUpState=0"
    )


def test_wm_start_with_temp_and_soil():
    assert washing_machine_start(
        program=13, temp=40, soil_level=2, spin_target=15, spin_default=10
    ) == (
        "Write=1&Pa=0&Sel=0&PrNm=13&StSt=1&Temp=40&SLevTgt=2&SpdTgt=15&SpdDef=10"
        "&Stm=0&RecipeId=0&CheckUpState=0"
    )


def test_wm_stop():
    assert washing_machine_stop(program=2) == "Write=1&StSt=0&DelMd=0&PrNm=2"
    assert washing_machine_stop(program=10) == "Write=1&StSt=0&DelMd=0&PrNm=10"


def test_wm_pause_resume():
    assert washing_machine_pause() == "Write=1&Pa=1"
    assert washing_machine_resume() == "Write=1&Pa=0"
