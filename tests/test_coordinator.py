"""Polling behaviour: rate-limit friendliness, stale data, setup retry and options."""

from __future__ import annotations

from datetime import timedelta

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from custom_components.growatt_thor_cloud.api import GrowattThorApiError

from .common import setup_integration, state


async def test_outage_keeps_data_then_backs_off(hass: HomeAssistant, mock_api, freezer) -> None:
    """Short outages keep the last values; polling slows down and recovers on success."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    mock_api.async_get_chargers.side_effect = GrowattThorApiError("rate limited")

    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=120)
    assert state(hass, "sensor", "status").state == "charging"

    freezer.tick(timedelta(minutes=6))  # Past the grace period.
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=300)
    assert state(hass, "sensor", "status").state == "unavailable"

    mock_api.async_get_chargers.side_effect = None
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=60)
    assert state(hass, "sensor", "status").state == "charging"


async def test_settings_read_every_five_minutes(hass: HomeAssistant, mock_api, freezer) -> None:
    """Settings are re-read on a slow timer, or right after a write from HA."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    assert mock_api.async_get_config.await_count == 1

    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == 1

    freezer.tick(timedelta(minutes=5))
    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == 2

    await coordinator.async_refresh_after_write()
    await hass.async_block_till_done()
    assert mock_api.async_get_config.await_count == 3


async def test_setup_retries_when_cloud_is_down(hass: HomeAssistant, mock_api) -> None:
    """No data at startup: HA retries the setup later instead of failing for good."""
    mock_api.async_get_chargers.side_effect = GrowattThorApiError("timeout")
    entry = await setup_integration(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_options_polling_interval(hass: HomeAssistant, mock_api) -> None:
    """The polling interval is configurable within bounds and applies after reload."""
    entry = await setup_integration(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 10}
        )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 120}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval == timedelta(seconds=120)
