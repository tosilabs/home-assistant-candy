"""
Write command payloads for Candy/Haier appliances.

The write protocol is not officially documented; these payloads come from
community reverse-engineering and may need adjustment for some models. For
anything beyond pause/resume, the recommended path is the candy.send_command
service which lets the user pass arbitrary URL parameters.
"""
from typing import Mapping, Union

CommandParams = Mapping[str, Union[str, int]]

# Wi-Fi remote control flag, expected by most models when sending commands
PARAM_WIFI_STATUS = "WiFiStatus"

# Pause flag: 1 to pause a running cycle, 0 to resume
PARAM_PAUSE = "Pause"


def pause_payload() -> CommandParams:
    return {PARAM_WIFI_STATUS: 1, PARAM_PAUSE: 1}


def resume_payload() -> CommandParams:
    return {PARAM_WIFI_STATUS: 1, PARAM_PAUSE: 0}
