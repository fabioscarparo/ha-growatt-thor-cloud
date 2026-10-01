"""The Wallbox card, served by the integration and loaded on every dashboard."""

from __future__ import annotations

import json
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.growatt_thor_cloud.card import CARD_FILE, CARD_URL, async_register_card

ADD_JS = "custom_components.growatt_thor_cloud.card.add_extra_js_url"


async def test_card_served(hass: HomeAssistant, hass_client) -> None:
    """The card is served and added to the frontend under the integration's version."""
    assert await async_setup_component(hass, "http", {})
    hass.config.components.add("frontend")
    with patch(ADD_JS) as add_js:
        await async_register_card(hass)

    version = json.loads((CARD_FILE.parent.parent / "manifest.json").read_text())["version"]
    add_js.assert_called_once_with(hass, f"{CARD_URL}?v={version}")
    client = await hass_client()
    resp = await client.get(CARD_URL)
    assert resp.status == 200
    assert "thor-wallbox-card" in await resp.text()


async def test_card_needs_frontend(hass: HomeAssistant) -> None:
    """Without the web server and the frontend there is nothing to register."""
    with patch(ADD_JS) as add_js:
        await async_register_card(hass)
    add_js.assert_not_called()
