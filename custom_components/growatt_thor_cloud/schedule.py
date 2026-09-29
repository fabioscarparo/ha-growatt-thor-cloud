"""Scheduled starts (session limits, reservations) and Boost.

Entities stage values in a ChargePlan; the dashboard buttons and switches and
the actions all send them through these helpers, so both behave the same.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import replace
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.util import dt as dt_util

from .api import GrowattThorError
from .charge_mode import (
    MODE_FAST,
    MODE_OFF_PEAK,
    MODE_PV_LINKAGE,
    charge_mode_fields,
    cheapest_period_time,
)
from .const import CONNECTOR_ID, LIMIT_COST, LIMIT_DURATION, LIMIT_ENERGY
from .coordinator import ChargePlan, GrowattThorCoordinator, ThorCharger

# Plan limit type -> session limit key (cKey), and back.
LIMIT_KEYS = {"cost": LIMIT_COST, "energy": LIMIT_ENERGY, "duration": LIMIT_DURATION}
LIMIT_TYPES = {key: limit for limit, key in LIMIT_KEYS.items()}

# Boost exists in PV Linkage (manual or smart) and Off-peak (smart only).
BOOST_MODES = (MODE_PV_LINKAGE, MODE_OFF_PEAK)


class PlanError(ValueError):
    """The staged values cannot be sent as they are."""


@contextmanager
def ha_errors(action: str) -> Iterator[None]:
    """Report invalid values as validation errors and cloud failures as action errors."""
    try:
        yield
    except ValueError as err:
        raise ServiceValidationError(str(err)) from err
    except GrowattThorError as err:
        raise HomeAssistantError(f"{action}: {err}") from err


# --- Scheduled start ------------------------------------------------------


def limit_fields(plan: ChargePlan) -> tuple[str | None, str | None]:
    """Session limit as (cKey, cValue); (None, None) when charging without a limit."""
    if plan.limit == "none":
        return None, None
    value = getattr(plan, f"limit_{plan.limit}")
    if value is None:
        raise PlanError(f"Set the {plan.limit} limit value first")
    if plan.limit == "duration":
        return LIMIT_DURATION, str(int(value))
    return LIMIT_KEYS[plan.limit], f"{value:g}"


def next_start(at: time, now: datetime) -> datetime:
    """Next occurrence of `at` in local time: today, or tomorrow if already past."""
    start = now.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    return start if start > now else start + timedelta(days=1)


async def async_start(coordinator: GrowattThorCoordinator, sn: str, plan: ChargePlan) -> None:
    """Fast: start now, or reserve a start at plan.start_time (once or every day)."""
    if coordinator.data[sn].charge_mode.get("mode") != MODE_FAST:
        raise PlanError("Scheduled charging is only available in Fast mode")
    key, value = limit_fields(plan)
    if plan.start != "now" and plan.start_time is None:
        raise PlanError("Set the start time first")
    if plan.start == "now":
        await coordinator.api.async_start_charging(sn, CONNECTOR_ID, key, value)
    else:
        await coordinator.api.async_reserve_charging(
            sn,
            CONNECTOR_ID,
            next_start(plan.start_time, dt_util.now()),
            every_day=plan.start == "every_day",
            limit_key=key,
            limit_value=value,
        )


async def async_cancel_reservations(coordinator: GrowattThorCoordinator, sn: str) -> None:
    """Cancel every reservation of the charger."""
    reservations = coordinator.data[sn].reservations
    if not reservations:
        raise PlanError("No reservation to cancel")
    for reservation in reservations:
        await coordinator.api.async_cancel_reservation(sn, reservation)


def next_reservation(charger: ThorCharger) -> tuple[datetime, dict[str, Any]] | None:
    """Earliest upcoming reservation as (local start, raw entry)."""
    now = dt_util.now()
    upcoming: list[tuple[datetime, dict[str, Any]]] = []
    for reservation in charger.reservations:
        if str(reservation.get("loopType")) == "0":
            # Every day: next occurrence of loopValue ("HH:MM").
            at = _parse_time(str(reservation.get("loopValue", "")))
            if at:
                upcoming.append((next_start(at, now), reservation))
            continue
        # expiryDate is local wall-clock time with a literal "Z", not UTC.
        raw = str(reservation.get("expiryDate", ""))[:16]
        try:
            start = datetime.strptime(raw, "%Y-%m-%dT%H:%M").replace(tzinfo=now.tzinfo)
        except ValueError:
            continue
        if start > now:
            upcoming.append((start, reservation))
    return min(upcoming, key=lambda item: item[0]) if upcoming else None


# --- Boost ----------------------------------------------------------------


def is_boost_on(charger: ThorCharger) -> bool:
    return str(charger.charge_mode.get("boost")) == "1"


def effective_plan(coordinator: GrowattThorCoordinator, sn: str) -> ChargePlan:
    """The staged plan, aligned with the charger where it matters.

    Boost settings follow the charger while Boost runs, off-peak slots while in
    Off-peak (and until the user stages their own): entities stay truthful and
    edits start from what the charger actually does.
    """
    plan = coordinator.plan(sn)
    charger = coordinator.data.get(sn)
    if charger is None:
        return plan
    _sync_off_peak(plan, charger)
    if is_boost_on(charger):
        _sync_boost(plan, charger)
    return plan


def _sync_boost(plan: ChargePlan, charger: ThorCharger) -> None:
    plan.boost_type = charger.charge_mode.get("boostType") or plan.boost_type
    params = dict(
        part.split("=", 1)
        for part in str(charger.charge_mode.get("config") or "").split("&")
        if "=" in part
    )
    window = params.get("time1", "").split("-")
    if len(window) == 2 and (start := _parse_time(window[0])) and (end := _parse_time(window[1])):
        plan.boost_from, plan.boost_to = start, end
    if departure := _parse_time(params.get("contime", "")):
        plan.boost_departure = departure
    with suppress(KeyError, ValueError):
        plan.boost_energy = float(params["energy"])


def boost_fields(charger: ThorCharger, plan: ChargePlan, enabled: bool) -> dict[str, Any]:
    """chargeMode update turning Boost on with the plan's settings, or off."""
    mode = charger.charge_mode.get("mode")
    if mode not in BOOST_MODES:
        raise PlanError("Boost is only available in PV Linkage and Off-peak")
    if not enabled:
        return charge_mode_fields(charger, mode, boost="0", config="")
    # Off-peak only has smart Boost.
    boost_type = "smart" if mode == MODE_OFF_PEAK else plan.boost_type
    if boost_type == "manual":
        if plan.boost_from is None or plan.boost_to is None:
            raise PlanError("Set the Boost from and to times first")
        config = f"time1={plan.boost_from:%H:%M}-{plan.boost_to:%H:%M}"
    else:
        if plan.boost_departure is None or plan.boost_energy is None:
            raise PlanError("Set the Boost departure time and energy first")
        config = f"contime={plan.boost_departure:%H:%M}&energy={plan.boost_energy:g}"
    return charge_mode_fields(charger, mode, boost="1", boostType=boost_type, config=config)


async def async_set_boost(
    coordinator: GrowattThorCoordinator, sn: str, plan: ChargePlan, enabled: bool
) -> None:
    """Send Boost on/off and mirror it locally until the next refresh."""
    charger = coordinator.data[sn]
    fields = boost_fields(charger, plan, enabled)
    await coordinator.api.async_set_charge_mode(sn, CONNECTOR_ID, fields)
    charger.charge_mode.update(fields)


# --- Off-peak slots -------------------------------------------------------

# HA exposes 3 slots; the app allows 5, extra ones set there are kept untouched.
OFF_PEAK_SLOTS = 3


def _parse_periods(period_time: str) -> list[tuple[time, time]]:
    """"time1=HH:MM-HH:MM&time2=..." as [(from, to), ...], skipping malformed parts."""
    slots = []
    for part in period_time.split("&"):
        start, _, end = part.partition("=")[2].partition("-")
        if (slot_from := _parse_time(start)) and (slot_to := _parse_time(end)):
            slots.append((slot_from, slot_to))
    return slots


def _sync_off_peak(plan: ChargePlan, charger: ThorCharger) -> None:
    """Follow the charger's slots while in Off-peak, or until the user stages their own.

    Outside Off-peak the default is the last slots used, else the cheapest
    tariff slots, like the app.
    """
    live = charger.charge_mode.get("mode") == MODE_OFF_PEAK
    if plan.off_peak_staged and not live:
        return
    slots = _parse_periods(str(charger.charge_mode.get("G_PeriodTime") or ""))
    if not slots and not live:
        slots = _parse_periods(cheapest_period_time(charger))
    if not slots:
        return
    midnight = time(0, 0)
    for index in range(OFF_PEAK_SLOTS):
        slot_from, slot_to = slots[index] if index < len(slots) else (midnight, midnight)
        setattr(plan, f"off_peak_{index + 1}_from", slot_from)
        setattr(plan, f"off_peak_{index + 1}_to", slot_to)
    plan.off_peak_extra = [f"{a:%H:%M}-{b:%H:%M}" for a, b in slots[OFF_PEAK_SLOTS:]]


def period_time(plan: ChargePlan) -> str:
    """G_PeriodTime for the used slots (start != end) plus extra ones set in the app."""
    windows = []
    for index in range(1, OFF_PEAK_SLOTS + 1):
        slot_from = getattr(plan, f"off_peak_{index}_from")
        slot_to = getattr(plan, f"off_peak_{index}_to")
        if slot_from != slot_to:
            windows.append(f"{slot_from:%H:%M}-{slot_to:%H:%M}")
    windows += plan.off_peak_extra
    if not windows:
        raise PlanError("Set at least one off-peak slot with a start different from its end")
    return "&".join(f"time{i}={window}" for i, window in enumerate(windows, 1))


def off_peak_fields(charger: ThorCharger, plan: ChargePlan) -> dict[str, Any]:
    """chargeMode update to Off-peak with the plan's slots."""
    return charge_mode_fields(charger, MODE_OFF_PEAK, G_PeriodTime=period_time(plan))


async def async_set_off_peak(
    coordinator: GrowattThorCoordinator, sn: str, plan: ChargePlan
) -> None:
    """Send the off-peak slots and mirror them locally until the next refresh."""
    charger = coordinator.data[sn]
    fields = off_peak_fields(charger, plan)
    await coordinator.api.async_set_charge_mode(sn, CONNECTOR_ID, fields)
    charger.charge_mode.update(fields)


# --- Staged values --------------------------------------------------------

# Which live setting a staged value belongs to: resent at once while in use.
LIVE_BOOST = "boost"
LIVE_OFF_PEAK = "off_peak"


async def async_update_plan(
    coordinator: GrowattThorCoordinator,
    sn: str,
    field: str,
    value: Any,
    live: str | None = None,
) -> None:
    """Stage one plan value; Boost and off-peak settings are resent while in use."""
    plan = effective_plan(coordinator, sn)
    charger = coordinator.data[sn]
    updated = replace(plan, **{field: value})
    sent = False
    if live == LIVE_BOOST and is_boost_on(charger):
        await async_set_boost(coordinator, sn, updated, True)
        sent = True
    elif live == LIVE_OFF_PEAK and charger.charge_mode.get("mode") == MODE_OFF_PEAK:
        await async_set_off_peak(coordinator, sn, updated)
        sent = True
    setattr(plan, field, value)
    if live == LIVE_OFF_PEAK:
        plan.off_peak_staged = True
    coordinator.async_update_listeners()
    if sent:
        await coordinator.async_refresh_after_write()


def _parse_time(value: str) -> time | None:
    """Parse "H:MM" / "HH:MM"; None if malformed."""
    try:
        hours, minutes = value.strip().split(":")[:2]
        return time(int(hours), int(minutes))
    except ValueError:
        return None
