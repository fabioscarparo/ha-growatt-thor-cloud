"""Setting the charger's clock from Home Assistant: time zone and daylight saving.

The charger runs Off-peak slots, Boost windows and scheduled starts on its own clock: a
time zone from Growatt's list (sysTimeZone, e.g. "UTC+1") plus a daylight saving period
set by date (G_DaylightSavingTime, "MM-DD&MM-DD"). These tests check:

- what Home Assistant's time zone translates to (clock.zone_for, daylight_saving_for);
- the manual entities: "General - Time zone" (select) and the daylight saving start and
  end (text), with the values they refuse;
- "General - Clock from Home Assistant" (switch): it sets both right away, keeps them
  aligned (the daylight saving dates move on every year), survives restarts, stays off
  when no time zone of the charger matches, and makes the manual entities unavailable;
- the "Fix" button of the clock warning in Repairs, through Home Assistant's own flow API.

Home Assistant runs in Europe/Rome on 6 November 2026, after that year's daylight saving:
the charger should be on "UTC+1" with the 2027 period, "03-28&10-31". The fixture charger
is on "UTC+2" without daylight saving (conftest.CONFIG).
"""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

import pytest

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.growatt_thor_cloud.clock import ClockError, daylight_saving_for, zone_for
from custom_components.growatt_thor_cloud.const import DOMAIN

from .common import call, set_config, setup_integration, state
from .conftest import SN, TIME_ZONES

ISSUE_ID = f"time_zone_{SN}"
# A day after the 2026 daylight saving period in Italy.
NOW = "2026-11-06 10:00:00+01:00"


@pytest.fixture
async def rome(hass: HomeAssistant, freezer) -> None:
    """Home Assistant in Europe/Rome on NOW."""
    await hass.config.async_set_time_zone("Europe/Rome")
    freezer.move_to(NOW)


def _writes(mock_api) -> list[tuple[str, object]]:
    """The settings written so far, as (key, value)."""
    return [(args[1], args[2]) for args, _ in mock_api.async_set_config.call_args_list]


@pytest.mark.parametrize(
    ("zone", "day", "expected_zone", "expected_daylight"),
    [
        # After the 2026 period: the 2027 one (last Sundays of March and October).
        ("Europe/Rome", date(2026, 11, 6), "UTC+1", "03-28&10-31"),
        # During a period: that period.
        ("Europe/Rome", date(2026, 6, 1), "UTC+1", "03-29&10-25"),
        ("Europe/London", date(2026, 11, 6), "UTC", "03-28&10-31"),
        ("America/New_York", date(2026, 11, 6), "UTC-5", "03-14&11-07"),
        # Southern hemisphere: the period runs across the new year.
        ("Australia/Sydney", date(2026, 11, 6), "UTC+10", "10-04&04-04"),
        # No daylight saving.
        ("Asia/Kolkata", date(2026, 11, 6), "UTC+5:30", "00-00&00-00"),
    ],
)
def test_clock_for_home_assistant(
    zone: str, day: date, expected_zone: str, expected_daylight: str
) -> None:
    """Home Assistant's time zone maps to a zone of Growatt's list and a daylight saving period."""
    tz = ZoneInfo(zone)
    assert zone_for(tz, day, TIME_ZONES) == expected_zone
    assert daylight_saving_for(tz, day) == expected_daylight


def test_no_matching_zone() -> None:
    """A standard offset missing from Growatt's list cannot be set (Nepal is UTC+5:45)."""
    with pytest.raises(ClockError):
        zone_for(ZoneInfo("Asia/Kathmandu"), date(2026, 11, 6), TIME_ZONES)


async def test_time_zone_select(hass: HomeAssistant, mock_api) -> None:
    """The select offers Growatt's zones, shows the charger's and writes the one picked."""
    await setup_integration(hass)
    select = state(hass, "select", "time_zone")
    assert select.state == "UTC+2"
    assert select.attributes["options"] == TIME_ZONES

    await call(hass, "select", "select_option", "time_zone", option="UTC+1")
    mock_api.async_set_config.assert_awaited_once_with(SN, "sysTimeZone", "UTC+1")
    assert state(hass, "select", "time_zone").state == "UTC+1"


async def test_daylight_saving_dates(hass: HomeAssistant, mock_api) -> None:
    """Each date is written with the other one as it is; empty means not set."""
    await setup_integration(hass)
    assert state(hass, "text", "daylight_saving_start").state == ""
    assert state(hass, "text", "daylight_saving_end").state == ""

    await call(hass, "text", "set_value", "daylight_saving_start", value="03-28")
    await call(hass, "text", "set_value", "daylight_saving_end", value="10-31")
    assert _writes(mock_api) == [
        ("G_DaylightSavingTime", "03-28&00-00"),
        ("G_DaylightSavingTime", "03-28&10-31"),
    ]
    assert state(hass, "text", "daylight_saving_end").state == "10-31"


@pytest.mark.parametrize("value", ["13-01", "02-30", "10-31"], ids=["month", "day", "same as start"])
async def test_daylight_saving_refused(hass: HomeAssistant, mock_api, value: str) -> None:
    """Days that do not exist, and an end equal to the start, are refused before sending."""
    set_config(mock_api, G_DaylightSavingTime="10-31&00-00")
    await setup_integration(hass)

    with pytest.raises(ServiceValidationError):
        await call(hass, "text", "set_value", "daylight_saving_end", value=value)
    mock_api.async_set_config.assert_not_awaited()


@pytest.mark.usefixtures("rome")
async def test_clock_from_home_assistant(hass: HomeAssistant, mock_api) -> None:
    """Turning the switch on sets Home Assistant's clock; the manual entities step aside."""
    await setup_integration(hass)

    await call(hass, "switch", "turn_on", "clock_from_ha")
    assert _writes(mock_api) == [
        ("sysTimeZone", "UTC+1"),
        ("G_DaylightSavingTime", "03-28&10-31"),
    ]
    assert state(hass, "switch", "clock_from_ha").state == "on"
    for domain, key in (
        ("select", "time_zone"),
        ("text", "daylight_saving_start"),
        ("text", "daylight_saving_end"),
    ):
        assert state(hass, domain, key).state == "unavailable"

    await call(hass, "switch", "turn_off", "clock_from_ha")
    assert state(hass, "select", "time_zone").state == "UTC+1"


@pytest.mark.usefixtures("rome")
async def test_daylight_saving_renewed(hass: HomeAssistant, mock_api, freezer) -> None:
    """While the switch is on, the dates move to the next period once one is over."""
    entry = await setup_integration(hass)
    await call(hass, "switch", "turn_on", "clock_from_ha")
    # The charger took the values.
    set_config(mock_api, sysTimeZone="UTC+1", G_DaylightSavingTime="03-28&10-31")
    mock_api.async_set_config.reset_mock()

    freezer.move_to("2027-11-02 10:00:00+01:00")  # After the 2027 period.
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    # 2028: last Sundays of March and October.
    assert _writes(mock_api) == [("G_DaylightSavingTime", "03-26&10-29")]


@pytest.mark.usefixtures("rome")
async def test_switch_restored(hass: HomeAssistant, mock_api) -> None:
    """Left on before a restart, the switch keeps aligning the clock."""
    mock_restore_cache(
        hass, [State(f"switch.{SN.lower()}_general_clock_from_home_assistant", "on")]
    )
    entry = await setup_integration(hass)
    assert state(hass, "switch", "clock_from_ha").state == "on"

    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert _writes(mock_api) == [
        ("sysTimeZone", "UTC+1"),
        ("G_DaylightSavingTime", "03-28&10-31"),
    ]


async def test_switch_stays_off_without_matching_zone(
    hass: HomeAssistant, mock_api, freezer
) -> None:
    """When no zone of the charger matches Home Assistant's, nothing is written."""
    await hass.config.async_set_time_zone("Asia/Kathmandu")
    freezer.move_to(NOW)
    await setup_integration(hass)

    with pytest.raises(ServiceValidationError):
        await call(hass, "switch", "turn_on", "clock_from_ha")
    assert state(hass, "switch", "clock_from_ha").state == "off"
    mock_api.async_set_config.assert_not_awaited()


@pytest.mark.usefixtures("rome")
async def test_fix_from_repairs(hass: HomeAssistant, mock_api, hass_client) -> None:
    """The clock warning's Fix shows what will be set and sets it once confirmed."""
    await setup_integration(hass)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.is_fixable

    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    resp = await client.post(
        "/api/repairs/issues/fix", json={"handler": DOMAIN, "issue_id": ISSUE_ID}
    )
    form = await resp.json()
    assert form["step_id"] == "confirm"
    assert form["description_placeholders"] == {
        "name": SN,  # The fixture charger has no name.
        "zone": "UTC+2",
        "charger_offset": "+02:00",
        "ha_offset": "+01:00",
        "new_zone": "UTC+1",
        "new_daylight": "03-28 → 10-31",
    }

    resp = await client.post(f"/api/repairs/issues/fix/{form['flow_id']}", json={})
    assert (await resp.json())["type"] == "create_entry"
    assert _writes(mock_api) == [
        ("sysTimeZone", "UTC+1"),
        ("G_DaylightSavingTime", "03-28&10-31"),
    ]
