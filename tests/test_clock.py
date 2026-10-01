"""The charger's clock and the Repairs warning when it differs from Home Assistant's."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.growatt_thor_cloud.clock import (
    base_offset,
    charger_offset,
    format_offset,
)
from custom_components.growatt_thor_cloud.const import DOMAIN

from .common import set_config, setup_integration
from .conftest import SN

ISSUE_ID = f"time_zone_{SN}"


@pytest.mark.parametrize(
    ("zone", "offset"),
    [
        ("UTC+2", timedelta(hours=2)),
        ("UTC-3:30", -timedelta(hours=3, minutes=30)),
        ("GMT+5:45", timedelta(hours=5, minutes=45)),
        ("UTC", timedelta(0)),
        ("Europe/Rome", None),
        (None, None),
    ],
)
def test_base_offset(zone: str | None, offset: timedelta | None) -> None:
    assert base_offset(zone) == offset


def test_daylight_saving() -> None:
    """An hour is added between the dates; the switch days themselves are unknown."""
    config = {"sysTimeZone": "UTC+1", "G_DaylightSavingTime": "03-29&10-25"}
    assert charger_offset(config, date(2026, 10, 1)) == timedelta(hours=2)
    assert charger_offset(config, date(2026, 10, 25)) is None
    assert charger_offset(config, date(2026, 10, 26)) == timedelta(hours=1)
    assert charger_offset(config, date(2026, 1, 10)) == timedelta(hours=1)
    # Not set: the zone alone.
    config["G_DaylightSavingTime"] = "00-00&00-00"
    assert charger_offset(config, date(2026, 10, 1)) == timedelta(hours=1)
    # Southern hemisphere: the period runs across the new year.
    config = {"sysTimeZone": "UTC+10", "G_DaylightSavingTime": "10-04&04-05"}
    assert charger_offset(config, date(2026, 12, 25)) == timedelta(hours=11)
    assert charger_offset(config, date(2026, 6, 1)) == timedelta(hours=10)


def test_format_offset() -> None:
    assert format_offset(timedelta(hours=2)) == "+02:00"
    assert format_offset(-timedelta(hours=3, minutes=30)) == "-03:30"


async def test_clock_warning(hass: HomeAssistant, mock_api, freezer) -> None:
    """The warning follows the gap between the charger's clock and Home Assistant's."""
    await hass.config.async_set_time_zone("Europe/Rome")
    freezer.move_to("2026-10-01 10:00:00+02:00")
    entry = await setup_integration(hass)  # UTC+2 without daylight saving: right in summer.
    coordinator = entry.runtime_data
    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is None

    freezer.move_to("2026-10-26 10:00:00+01:00")  # Italy is back on UTC+1.
    await coordinator.async_refresh()
    issue = registry.async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.translation_key == "time_zone_mismatch"
    assert issue.translation_placeholders["charger_offset"] == "+02:00"
    assert issue.translation_placeholders["ha_offset"] == "+01:00"

    # Fixed on the charger: UTC+1 with daylight saving, read with the settings.
    set_config(mock_api, sysTimeZone="UTC+1", G_DaylightSavingTime="03-29&10-25")
    freezer.tick(timedelta(minutes=5))
    await coordinator.async_refresh()
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is None


async def test_clock_warning_withdrawn_on_unload(
    hass: HomeAssistant, mock_api, freezer
) -> None:
    await hass.config.async_set_time_zone("Europe/Rome")
    freezer.move_to("2026-12-01 10:00:00+01:00")
    entry = await setup_integration(hass)
    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is not None

    await hass.config_entries.async_unload(entry.entry_id)
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is None
