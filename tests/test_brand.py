"""The integration's own icon, served by Home Assistant's brands API."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import setup_integration


@pytest.mark.parametrize(("image", "size"), [("icon.png", 256), ("icon@2x.png", 512)])
async def test_brand_icon(
    hass: HomeAssistant, hass_client, mock_api, image: str, size: int
) -> None:
    """The brand folder is picked up: the icon is a PNG of the expected size."""
    await setup_integration(hass)
    assert await async_setup_component(hass, "brands", {})
    client = await hass_client()

    resp = await client.get(f"/api/brands/integration/growatt_thor_cloud/{image}")

    assert resp.status == 200
    assert resp.content_type == "image/png"
    body = await resp.read()
    assert body[:8] == b"\x89PNG\r\n\x1a\n"
    # PNG header: width and height are big-endian ints at bytes 16-24.
    assert int.from_bytes(body[16:20], "big") == size
    assert int.from_bytes(body[20:24], "big") == size
