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
from .charge_mode import MODE_OFF_PEAK, MODE_PV_LINKAGE, charge_mode_fields
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
    if plan.limit == "cost":
        return LIMIT_COST, f"{plan.limit_cost:g}"
    if plan.limit == "energy":
        return LIMIT_ENERGY, f"{plan.limit_energy:g}"
    if plan.limit == "duration":
        return LIMIT_DURATION, str(int(plan.limit_duration))
    return None, None


def next_start(at: time, now: datetime) -> datetime:
    """Next occurrence of `at` in local time: today, or tomorrow if already past."""
    start = now.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    return start if start > now else start + timedelta(days=1)


async def async_start(coordinator: GrowattThorCoordinator, sn: str, plan: ChargePlan) -> None:
    """Start now, or reserve a start at plan.start_time (once or every day)."""
    key, value = limit_fields(plan)
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
    """The staged plan, with the Boost fields taken from the charger while Boost runs.

    Keeps the entities truthful and makes edits start from what the charger
    actually does, not from stale staged values.
    """
    plan = coordinator.plan(sn)
    charger = coordinator.data.get(sn)
    if charger is None or not is_boost_on(charger):
        return plan
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
    return plan


def boost_fields(charger: ThorCharger, plan: ChargePlan, enabled: bool) -> dict[str, Any]:
    """chargeMode update turning Boost on with the plan's settings, or off."""
    mode = charger.charge_mode.get("mode")
    if mode not in BOOST_MODES:
        raise PlanError("Boost is only available in PV Linkage and Off-peak")
    if not enabled:
        return charge_mode_fields(charger, mode, boost="0", config="")
    if plan.boost_type == "manual":
        if mode == MODE_OFF_PEAK:
            raise PlanError("Off-peak only supports smart Boost")
        config = f"time1={plan.boost_from:%H:%M}-{plan.boost_to:%H:%M}"
    else:
        config = f"contime={plan.boost_departure:%H:%M}&energy={plan.boost_energy:g}"
    return charge_mode_fields(
        charger, mode, boost="1", boostType=plan.boost_type, config=config
    )


async def async_set_boost(
    coordinator: GrowattThorCoordinator, sn: str, plan: ChargePlan, enabled: bool
) -> None:
    """Send Boost on/off and mirror it locally until the next refresh."""
    charger = coordinator.data[sn]
    fields = boost_fields(charger, plan, enabled)
    await coordinator.api.async_set_charge_mode(sn, CONNECTOR_ID, fields)
    charger.charge_mode.update(fields)


async def async_update_plan(
    coordinator: GrowattThorCoordinator, sn: str, field: str, value: Any, boost: bool
) -> None:
    """Stage one plan value; a Boost setting changed while Boost runs is resent at once."""
    plan = effective_plan(coordinator, sn)
    if boost and is_boost_on(coordinator.data[sn]):
        await async_set_boost(coordinator, sn, replace(plan, **{field: value}), True)
        setattr(plan, field, value)
        coordinator.async_update_listeners()
        await coordinator.async_refresh_after_write()
        return
    setattr(plan, field, value)
    coordinator.async_update_listeners()


def _parse_time(value: str) -> time | None:
    """Parse "H:MM" / "HH:MM"; None if malformed."""
    try:
        hours, minutes = value.strip().split(":")[:2]
        return time(int(hours), int(minutes))
    except ValueError:
        return None
