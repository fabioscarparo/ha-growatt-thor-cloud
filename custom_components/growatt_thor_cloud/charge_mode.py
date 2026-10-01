"""Charge mode (Fast / PV Linkage / Off-peak) update payloads.

A mode change sends the whole mode object: Fast needs nothing else, PV Linkage
carries the meter setup and the allowed grid import, Off-peak carries its time
slots. Every update (mode, Boost, grid import, slots) is built here, so the
rules on when the mode may change live here too.
"""

from __future__ import annotations

from typing import Any

from .coordinator import ThorCharger
from .entity import to_float

MODE_FAST = "fast"
MODE_OFF_PEAK = "offPeak"
MODE_PV_LINKAGE = "pvLinkage"


def supported_modes(charger: ThorCharger) -> list[str]:
    """Modes the charger offers.

    Chargers reporting neither load balancing nor low-rate (off-peak) support
    run Fast only; PV Linkage also needs isSupportPL.
    """
    if not (
        charger.supports("isSupportLoadBalancing") or charger.supports("isSupportLowRateMode")
    ):
        return [MODE_FAST]
    if charger.supports("isSupportPL"):
        return [MODE_FAST, MODE_PV_LINKAGE, MODE_OFF_PEAK]
    return [MODE_FAST, MODE_OFF_PEAK]


def check_mode_change(charger: ThorCharger) -> None:
    """Raise ValueError when the mode and its settings must not change now."""
    if charger.shared:
        raise ValueError("Only the charger's owner can change its charge mode")
    if charger.in_session:
        raise ValueError("Stop charging before changing the charge mode or its settings")


def format_kw(value: object) -> str:
    """Grid import in kW as sent in mode updates: plain decimal string ("0", "1.4")."""
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

    The current Boost and grid import are kept only when staying in the same
    mode; a mode switch starts from the defaults (Boost off; PV Linkage:
    manual type, no grid import; Off-peak: smart type). Off-peak uses the
    given G_PeriodTime, else the last slots used, else the cheapest tariff
    slots. Raises ValueError when a required value is missing, during a
    session and on chargers only shared with the account.
    """
    check_mode_change(charger)
    if mode == MODE_FAST:
        return {"mode": MODE_FAST, **overrides}

    current = charger.charge_mode
    same_mode = current.get("mode") == mode
    fields: dict[str, Any] = {
        "mode": mode,
        "boost": str(current.get("boost") or 0) if same_mode else "0",
        "config": (current.get("config") or "") if same_mode else "",
    }
    if mode == MODE_PV_LINKAGE:
        fields["boostType"] = (current.get("boostType") or "manual") if same_mode else "manual"
        # The meter setup comes from the charger config; PV Linkage cannot work
        # without a grid sampling device.
        sampling = charger.config.get(
            "G_ExternalSamplingCurWring", current.get("G_ExternalSamplingCurWring")
        )
        if sampling is None or str(sampling) in ("", "-1"):
            raise ValueError("No grid sampling device (CT or meter) is set on the charger")
        fields["G_ExternalSamplingCurWring"] = str(sampling)
        fields["G_PowerMeterType"] = (
            charger.config.get("G_PowerMeterType") or current.get("G_PowerMeterType") or ""
        )
        # "0" = PV surplus only, the default when coming from another mode.
        fields["importGrid"] = format_kw(current.get("importGrid")) if same_mode else "0"
    elif mode == MODE_OFF_PEAK:
        # Smart is the only Boost type in Off-peak.
        fields["boostType"] = "smart"
        period = (
            overrides.get("G_PeriodTime")
            or current.get("G_PeriodTime")
            or cheapest_period_time(charger)
        )
        if not period:
            raise ValueError("No off-peak time slots configured")
        fields["G_PeriodTime"] = period
    fields.update(overrides)
    return fields
