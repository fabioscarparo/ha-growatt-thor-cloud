"""Growatt THOR EV charger integration (Growatt cloud API)."""

from __future__ import annotations

from homeassistant.const import CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrowattThorApi
from .const import CONF_PASSWORD_HASH
from .coordinator import GrowattThorConfigEntry, GrowattThorCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: GrowattThorConfigEntry) -> bool:
    """Create the API client and coordinator, then set up all platforms."""
    api = GrowattThorApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD_HASH],
    )
    coordinator = GrowattThorCoordinator(hass, entry, api)
    # Fetch once before adding entities: they are created from the chargers found here.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GrowattThorConfigEntry) -> bool:
    """Unload all platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
