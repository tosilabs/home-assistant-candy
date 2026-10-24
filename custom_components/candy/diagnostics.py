"""Download a bounded Start diagnostic without credentials or connection details."""
from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_KEY_COORDINATOR, DOMAIN
from .start_status import status_snapshot


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_KEY_COORDINATOR]
    return {
        "status_fresh": coordinator.last_update_success,
        "status": status_snapshot(coordinator.data),
        "last_start": deepcopy(data.get("last_start")),
        "note": "Cycle activity does not confirm the identity of a downloaded recipe.",
    }
