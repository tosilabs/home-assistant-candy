"""Reject explicit device write failures, including HTTP-200 error responses."""
import json


def validate_write_response(text: str) -> None:
    normalized = text.upper().replace("_", " ").replace("-", " ")
    if "BAD REQUEST" in normalized:
        raise ValueError("Device rejected the write command: BAD REQUEST")
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return  # Empty/unknown acknowledgments still require a status refresh.
    if not isinstance(data, dict):
        return
    for key in ("response", "result", "status"):
        value = data.get(key)
        if isinstance(value, str) and value.strip().upper() in (
            "ERROR", "FAIL", "FAILED", "FAILURE", "NACK", "REJECTED", "NOT ACCEPTED"
        ):
            raise ValueError("Device explicitly rejected the write command")
    if data.get("success") is False or data.get("accepted") is False:
        raise ValueError("Device explicitly rejected the write command")
