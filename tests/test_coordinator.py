"""Polling behaviour: rate-limit friendliness, stale data, setup retry and options."""

from __future__ import annotations

from datetime import timedelta

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from custom_components.growatt_thor_cloud.api import GrowattThorApiError

from .common import call, set_charging, setup_integration, state


async def test_outage_keeps_data_then_backs_off(hass: HomeAssistant, mock_api, freezer) -> None:
    """Short outages keep the last values; polling slows down and recovers on success."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    mock_api.async_get_chargers.side_effect = GrowattThorApiError("rate limited")

    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=120)
    assert state(hass, "sensor", "status").state == "available"

    freezer.tick(timedelta(minutes=6))  # Past the grace period.
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=300)
    assert state(hass, "sensor", "status").state == "unavailable"

    mock_api.async_get_chargers.side_effect = None
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=60)
    assert state(hass, "sensor", "status").state == "available"


async def test_settings_read_every_five_minutes(hass: HomeAssistant, mock_api, freezer) -> None:
    """Settings are re-read on a slow timer, not right after a write from HA."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    assert mock_api.async_get_config.await_count == 1

    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == 1

    freezer.tick(timedelta(minutes=5))
    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == 2

    # The charger has not applied a write yet: reading now would show the old value.
    await coordinator.async_refresh_after_write()
    await hass.async_block_till_done()
    assert mock_api.async_get_config.await_count == 2


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


async def test_data_update_does_not_reload(hass: HomeAssistant, mock_api) -> None:
    """A new password reloads through reauth only: no extra reload (and login) here."""
    entry = await setup_integration(hass)
    calls = mock_api.async_get_chargers.await_count
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "password_hash": "new-hash"}
    )
    await hass.async_block_till_done()
    assert mock_api.async_get_chargers.await_count == calls


async def test_entry_without_serial_is_skipped(hass: HomeAssistant, mock_api) -> None:
    """A malformed charger entry does not break the whole update."""
    mock_api.async_get_chargers.return_value = [
        {"name": "broken"},
        *mock_api.async_get_chargers.return_value,
    ]
    entry = await setup_integration(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert state(hass, "sensor", "status").state == "available"


async def test_start_stop_do_not_reread_settings(hass: HomeAssistant, mock_api) -> None:
    """Start and stop only change the session, so settings are not fetched again."""
    set_charging(mock_api)
    await setup_integration(hass)
    await call(hass, "switch", "turn_on", "charging")
    await call(hass, "switch", "turn_off", "charging")
    await hass.async_block_till_done()
    assert mock_api.async_get_config.await_count == 1


async def test_reservation_list_failure_is_not_fatal(hass: HomeAssistant, mock_api) -> None:
    """The reservation list is secondary: its failure keeps the rest of the data."""
    mock_api.async_get_reservations.side_effect = GrowattThorApiError("code 1")
    entry = await setup_integration(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert state(hass, "sensor", "status").state == "available"
    assert state(hass, "button", "cancel_reservation").state == "unavailable"


async def test_history_failure_is_not_fatal(hass: HomeAssistant, mock_api) -> None:
    """The charge history is secondary too: its failure keeps the rest of the data."""
    mock_api.async_get_sessions.side_effect = GrowattThorApiError("code 1")
    entry = await setup_integration(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert state(hass, "sensor", "last_session").state == "unknown"


async def test_settings_confirmed_after_write(hass: HomeAssistant, mock_api, freezer) -> None:
    """After a write the settings are read again once the charger has confirmed it."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    await coordinator.async_refresh_after_write()
    await hass.async_block_till_done()
    reads = mock_api.async_get_config.await_count

    freezer.tick(timedelta(seconds=60))
    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == reads  # Not confirmed yet.

    freezer.tick(timedelta(seconds=60))
    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == reads + 1  # Confirmed.

    freezer.tick(timedelta(seconds=60))
    await coordinator.async_refresh()
    assert mock_api.async_get_config.await_count == reads + 1  # Back to every 5 minutes.


async def test_written_setting_kept_until_confirmed(
    hass: HomeAssistant, mock_api, freezer
) -> None:
    """A written setting shows at once and is checked against the charger later."""
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    await call(hass, "switch", "turn_on", "warm_up")
    await hass.async_block_till_done()
    assert state(hass, "switch", "warm_up").state == "on"  # Not reverted by the refresh.

    # The charger never applied it: the confirming read shows the real value.
    freezer.tick(timedelta(seconds=120))
    await coordinator.async_refresh()
    assert state(hass, "switch", "warm_up").state == "off"
