"""Handle a partially initialized or already unloaded config entry."""
from types import SimpleNamespace

from custom_components.candy import async_unload_entry


async def test_unload_without_runtime_data(hass):
    assert await async_unload_entry(hass, SimpleNamespace(entry_id="not-initialized"))
