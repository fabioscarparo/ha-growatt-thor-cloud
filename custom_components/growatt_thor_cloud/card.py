"""Serve the Wallbox card and load it on every dashboard."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_FILE = Path(__file__).parent / "frontend" / "thor-wallbox-card.js"
CARD_URL = f"/{DOMAIN}/thor-wallbox-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and add it to the frontend.

    The URL carries the integration's version, so browsers fetch the new card
    after an update instead of a cached one.
    """
    if hass.http is None or "frontend" not in hass.config.components:
        # Without the web server and the frontend nothing could load the card.
        return
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")
