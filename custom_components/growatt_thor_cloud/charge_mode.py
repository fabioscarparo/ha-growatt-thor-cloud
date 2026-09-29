"""Charge mode (Fast / PV Linkage / Off-peak) update payloads.

A mode change sends the whole mode object, built the same way as the app's
mode pages: Fast needs nothing else, PV Linkage carries the meter setup and the
allowed grid import, Off-peak carries its time slots.
"""

from __future__ import annotations

from typing import Any

from .coordinator import ThorCharger
from .entity import to_float

MODE_FAST = "fast"
MODE_OFF_PEAK = "offPeak"
MODE_PV_LINKAGE = "pvLinkage"


def format_kw(value: object) -> str:
    """Grid import as the API stores it: plain decimal string ("0", "1.4")."""
    return f"{to_float(value) or 0.0:g}"


def cheapest_period_time(charger: ThorCharger) -> str:
    """Off-peak slots from the cheapest tariff, as "time1=HH:MM-HH:MM&time2=..."."""
    slots = [
        (price, slot.get("time"))
        for slot in charger.price_conf
        if (price := to_float(slot.get("price"))) is not None and slot.get("time")
    ]
    if not slots:
        return ""
    lowest = min(price for price, _ in slots)
    times = [time for price, time in slots if price == lowest]
    return "&".join(f"time{i}={time}" for i, time in enumerate(times, 1))


def charge_mode_fields(
    charger: ThorCharger, mode: str, **overrides: Any
) -> dict[str, Any]:
    """Fields for a chargeMode update to `mode`; `overrides` replace computed values.

    Raises ValueError for Off-peak when no tariff slots are configured.
    """
    if mode == MODE_FAST:
        return {"mode": MODE_FAST, **overrides}

    current = charger.charge_mode
    # Boost settings belong to the mode they were set in: keep them only when
    # the mode does not change (e.g. editing the grid import in PV Linkage).
    same_mode = current.get("mode") == mode
    fields: dict[str, Any] = {
        "mode": mode,
        "boost": str(current.get("boost") or 0) if same_mode else "0",
        "boostType": current.get("boostType") or "manual",
        "config": (current.get("config") or "") if same_mode else "",
    }
    if mode == MODE_PV_LINKAGE:
        # The meter setup comes from the charger config, which is authoritative.
        fields["G_ExternalSamplingCurWring"] = str(
            charger.config.get(
                "G_ExternalSamplingCurWring", current.get("G_ExternalSamplingCurWring", "")
            )
        )
        fields["G_PowerMeterType"] = (
            charger.config.get("G_PowerMeterType") or current.get("G_PowerMeterType") or ""
        )
        fields["importGrid"] = format_kw(current.get("importGrid"))
    elif mode == MODE_OFF_PEAK:
        # Reuse the slots chosen by the user, else default to the cheapest tariff.
        period = current.get("G_PeriodTime") or cheapest_period_time(charger)
        if not period:
            raise ValueError("No tariff time slots configured")
        fields["G_PeriodTime"] = period
    fields.update(overrides)
    return fields
