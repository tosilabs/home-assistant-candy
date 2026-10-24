"""Interpret fresh device status after a single Start request."""


def status_snapshot(status) -> dict:
    """Expose only appliance status, never connection details or encryption keys."""
    return {
        "machine_state": getattr(getattr(status, "machine_state", None), "name", None),
        "program_number": getattr(status, "program", None),
        "program_code": getattr(status, "program_code", None),
        "temperature": getattr(status, "temp", None),
        "spin_rpm": getattr(status, "spin_speed", None),
        "remaining_minutes": getattr(status, "remaining_minutes", None),
        "remote_control": getattr(status, "remote_control", None),
        "error": getattr(status, "error", None),
    }


def start_outcome(status, fresh: bool) -> str:
    """HTTP success alone is not evidence of a running wash or accepted recipe."""
    if not fresh:
        return "status_unavailable"
    snapshot = status_snapshot(status)
    if snapshot["machine_state"] == "ERROR" or snapshot["error"] not in (None, 0):
        return "device_error"
    if snapshot["machine_state"] == "RUNNING":
        return "running_recipe_unverified"
    if snapshot["machine_state"] == "DELAYED_START_PROGRAMMED":
        return "scheduled_recipe_unverified"
    return "not_confirmed"
