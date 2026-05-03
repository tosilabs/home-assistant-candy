"""Tests for plaintext command builders."""
from custom_components.candy.client.commands import (tumble_dryer_pause,
                                                     tumble_dryer_resume,
                                                     tumble_dryer_start,
                                                     tumble_dryer_stop,
                                                     washing_machine_pause,
                                                     washing_machine_resume,
                                                     washing_machine_start,
                                                     washing_machine_stop)


def test_wm_start_minimal():
    assert washing_machine_start(program=4) == (
        "Write=1&Pa=0&Sel=0&PrNm=4&StSt=1&OptMsk=0&Stm=0&RecipeId=0&CheckUpState=0"
    )


def test_wm_start_with_options():
    assert washing_machine_start(
        program=13, spin_target=15, spin_default=10
    ) == (
        "Write=1&Pa=0&Sel=0&PrNm=13&StSt=1&SpdTgt=15&SpdDef=10&OptMsk=0&Stm=0&RecipeId=0&CheckUpState=0"
    )


def test_wm_start_verified_capture():
    # Captured from Simply-Fi app: Resistant Cottons, 90°C / default 60°C,
    # spin 1300rpm / default 1000rpm, steam=High, OptMsk=67 (prewash+hygiene+3 extra rinses)
    assert washing_machine_start(
        program=13, temp_target=90, temp_default=60, spin_target=13, spin_default=10,
        opt_mask=67, steam=2,
    ) == (
        "Write=1&Pa=0&Sel=0&PrNm=13&StSt=1&TmpTgt=90&TmpDf=60&SpdTgt=13&SpdDef=10"
        "&OptMsk=67&Stm=2&RecipeId=0&CheckUpState=0"
    )


def test_wm_stop():
    assert washing_machine_stop(program=2) == "Write=1&StSt=0&DelMd=0&PrNm=2"
    assert washing_machine_stop(program=10) == "Write=1&StSt=0&DelMd=0&PrNm=10"


def test_wm_pause_resume():
    assert washing_machine_pause() == "Write=1&Pa=1"
    assert washing_machine_resume() == "Write=1&Pa=0"


def test_td_start_minimal():
    # Verified format captured from Simply-Fi app (Whites program)
    assert tumble_dryer_start(program=1, time=20, opt_mask=20, pr_str="Whites") == (
        "Write=1&PrNm=1&Time=20&OptMsk=20&RecipeId=0&PrStr=Whites&StSt=1"
    )


def test_td_start_no_time_mask():
    assert tumble_dryer_start(program=2) == (
        "Write=1&PrNm=2&Time=0&OptMsk=0&RecipeId=0&PrStr=&StSt=1"
    )


def test_td_stop():
    # Verified format captured from Simply-Fi app
    assert tumble_dryer_stop(program=1) == "Write=1&StSt=0&PrNm=1"
    assert tumble_dryer_stop(program=9) == "Write=1&StSt=0&PrNm=9"


def test_td_pause_resume():
    assert tumble_dryer_pause() == "Write=1&Pa=1"
    assert tumble_dryer_resume() == "Write=1&Pa=0"
