"""Growatt THOR EV charger integration (Growatt cloud API)."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import GrowattThorApi
from .const import CONF_PASSWORD_HASH, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import GrowattThorConfigEntry, GrowattThorCoordinator, clock_issue_id
from .services import async_setup_services

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the actions once; they look up the charger per call."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: GrowattThorConfigEntry) -> bool:
    """Create the API client and coordinator, then set up all platforms."""
    api = GrowattThorApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD_HASH],
    )
    coordinator = GrowattThorCoordinator(hass, entry, api)
    # Fetch once before adding entities: they are created from the chargers found here.
    # If the cloud is down or rate limiting, HA retries the setup later.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GrowattThorConfigEntry) -> bool:
    """Unload all platforms and withdraw this entry's clock warnings."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for sn in entry.runtime_data.data or {}:
            ir.async_delete_issue(hass, DOMAIN, clock_issue_id(sn))
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: GrowattThorConfigEntry) -> None:
    """Reload for a new polling interval.

    Other entry updates (a new password from reauth) already reload on their
    own; reloading here too would log in twice in a few seconds.
    """
    interval = timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    if interval != entry.runtime_data.base_interval:
        await hass.config_entries.async_reload(entry.entry_id)
