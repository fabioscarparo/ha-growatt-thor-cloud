"""The charger's clock: a fixed UTC offset plus a daylight saving period set by date.

Off-peak slots, Boost windows and scheduled starts run on this clock, so it
must match Home Assistant's local time.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, tzinfo
import re
from typing import Any

# "UTC+2", "UTC-3:30", "GMT+5:45" or plain "UTC".
_ZONE = re.compile(r"^(?:UTC|GMT)\s*(?:([+-])\s*(\d{1,2})(?::?(\d{2}))?)?$", re.IGNORECASE)
# Daylight saving start and end as "MM-DD&MM-DD"; "00-00&00-00" when not set.
_DST = re.compile(r"^(\d{2})-(\d{2})&(\d{2})-(\d{2})$")

# G_DaylightSavingTime without daylight saving.
NO_DAYLIGHT_SAVING = "00-00&00-00"
# Days read on each side of today to find a time zone's daylight saving periods.
_SCAN_DAYS = 400

type MonthDay = tuple[int, int]


class ClockError(ValueError):
    """Home Assistant's time zone cannot be set on the charger."""


def time_zone(config: dict[str, Any]) -> str | None:
    """The charger's time zone setting, e.g. "UTC+2"."""
    return config.get("sysTimeZone") or config.get("G_TimeZone") or None


def base_offset(zone: str | None) -> timedelta | None:
    """UTC offset of a zone like "UTC+2" or "UTC-3:30"; None if not understood."""
    match = _ZONE.match((zone or "").strip())
    if not match:
        return None
    sign, hours, minutes = match.groups()
    if sign is None:
        return timedelta(0)
    offset = timedelta(hours=int(hours), minutes=int(minutes or 0))
    return -offset if sign == "-" else offset


def dst_period(config: dict[str, Any]) -> tuple[MonthDay, MonthDay] | None:
    """Daylight saving start and end as (month, day); None when not set."""
    match = _DST.match(str(config.get("G_DaylightSavingTime") or ""))
    if not match:
        return None
    start_month, start_day, end_month, end_day = (int(part) for part in match.groups())
    if not (start_month and end_month):
        return None
    return (start_month, start_day), (end_month, end_day)


def charger_offset(config: dict[str, Any], day: date) -> timedelta | None:
    """UTC offset of the charger's clock on `day`.

    Daylight saving adds an hour between its start and end dates. None when
    the zone is not understood, and on the start and end days themselves,
    since the hour of the switch is not known.
    """
    offset = base_offset(time_zone(config))
    if offset is None:
        return None
    period = dst_period(config)
    if period is None:
        return offset
    today = (day.month, day.day)
    start, end = period
    if today in (start, end):
        return None
    # Southern hemisphere periods run across the new year.
    inside = start < today < end if start < end else (today > start or today < end)
    return offset + timedelta(hours=1) if inside else offset


def format_offset(offset: timedelta) -> str:
    """A UTC offset as "+02:00"."""
    minutes = int(offset.total_seconds()) // 60
    sign = "-" if minutes < 0 else "+"
    hours, minutes = divmod(abs(minutes), 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def _noon_offset(tz: tzinfo, day: date) -> timedelta:
    """UTC offset of `tz` at noon on `day`, after any daylight saving switch of that day."""
    return datetime.combine(day, time(12), tzinfo=tz).utcoffset() or timedelta(0)


def daylight_saving_for(tz: tzinfo, today: date) -> str:
    """G_DaylightSavingTime matching `tz`: the period in progress on `today`, else the next.

    The start is the first day on daylight time and the end the first day back on
    standard time, both read at noon ("03-28&10-31" for Europe/Rome in 2027). Without
    daylight saving, "00-00&00-00".
    """
    days = [today + timedelta(days=n) for n in range(-_SCAN_DAYS, _SCAN_DAYS + 1)]
    offsets = [_noon_offset(tz, day) for day in days]
    standard = min(offsets)
    start: date | None = None
    for day, offset in zip(days, offsets, strict=True):
        if offset > standard and start is None:
            start = day
        elif offset == standard and start is not None:
            if day > today:  # Ends after today: in progress or next.
                return f"{start:%m-%d}&{day:%m-%d}"
            start = None
    return NO_DAYLIGHT_SAVING


def zone_for(tz: tzinfo, today: date, zones: list[str]) -> str:
    """The zone of Growatt's list (timeZoneList2) with the standard UTC offset of `tz`."""
    standard = min(_noon_offset(tz, today + timedelta(days=n)) for n in range(-183, 183))
    for zone in zones:
        if base_offset(zone) == standard:
            return zone
    raise ClockError(f"No time zone of the charger matches UTC{format_offset(standard)}")
