"""Actions: scheduled start, reservation cancel and Boost.

They go through the same helpers as the dashboard entities; values passed to
an action are used as given, without touching the staged plan (except Boost,
whose entities must show what the charger runs).
"""

from __future__ import annotations

from dataclasses import replace

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .coordinator import ChargePlan, GrowattThorCoordinator
from .schedule import (
    async_cancel_reservations,
    async_set_boost,
    async_start,
    effective_plan,
    ha_errors,
)

ATTR_DEVICE_ID = "device_id"
POSITIVE = vol.All(vol.Coerce(float), vol.Range(min=0, min_included=False))

START_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional("limit", default="none"): vol.In(["none", "cost", "energy", "duration"]),
        vol.Optional("value"): POSITIVE,  # Currency, kWh or minutes, by limit.
        vol.Optional("start_time"): cv.time,  # Omitted = start now.
        vol.Optional("every_day", default=False): cv.boolean,
    }
)
CANCEL_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})
BOOST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required("enabled"): cv.boolean,
        vol.Optional("type"): vol.In(["manual", "smart"]),
        vol.Optional("from"): cv.time,
        vol.Optional("to"): cv.time,
        vol.Optional("departure"): cv.time,
        vol.Optional("energy"): POSITIVE,
    }
)
# Boost action field -> ChargePlan field.
BOOST_FIELDS = {
    "type": "boost_type",
    "from": "boost_from",
    "to": "boost_to",
    "departure": "boost_departure",
    "energy": "boost_energy",
}


def _resolve(hass: HomeAssistant, device_id: str) -> tuple[GrowattThorCoordinator, str]:
    """Coordinator and serial number of the charger behind a device id."""
    device = dr.async_get(hass).async_get(device_id)
    sn = next(
        (ident for domain, ident in (device.identifiers if device else ()) if domain == DOMAIN),
        None,
    )
    if device and sn:
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if (
                entry
                and entry.domain == DOMAIN
                and entry.state is ConfigEntryState.LOADED
                and sn in entry.runtime_data.data
            ):
                return entry.runtime_data, sn
    raise ServiceValidationError(f"{device_id} is not a loaded Growatt THOR charger")


async def _async_start(call: ServiceCall) -> None:
    coordinator, sn = _resolve(call.hass, call.data[ATTR_DEVICE_ID])
    limit = call.data["limit"]
    if limit != "none" and "value" not in call.data:
        raise ServiceValidationError(f"A value is required for a {limit} limit")
    if call.data["every_day"] and "start_time" not in call.data:
        raise ServiceValidationError("every_day needs a start_time")

    plan = ChargePlan(limit=limit)
    if limit != "none":
        value = call.data["value"]
        setattr(plan, f"limit_{limit}", int(value) if limit == "duration" else value)
    if "start_time" in call.data:
        plan.start = "every_day" if call.data["every_day"] else "at_time"
        plan.start_time = call.data["start_time"]
    with ha_errors("Could not start charging"):
        await async_start(coordinator, sn, plan)
    # Also re-reads the reservations, which a timed start creates.
    await coordinator.async_refresh_after_write()


async def _async_cancel(call: ServiceCall) -> None:
    coordinator, sn = _resolve(call.hass, call.data[ATTR_DEVICE_ID])
    with ha_errors("Could not cancel the reservation"):
        await async_cancel_reservations(coordinator, sn)
    await coordinator.async_refresh_after_write()


async def _async_boost(call: ServiceCall) -> None:
    coordinator, sn = _resolve(call.hass, call.data[ATTR_DEVICE_ID])
    plan = effective_plan(coordinator, sn)
    updates = {field: call.data[key] for key, field in BOOST_FIELDS.items() if key in call.data}
    with ha_errors("Could not set Boost"):
        await async_set_boost(coordinator, sn, replace(plan, **updates), call.data["enabled"])
    # Keep the Boost entities in line with what was just sent.
    for field, value in updates.items():
        setattr(plan, field, value)
    coordinator.async_update_listeners()
    await coordinator.async_refresh_after_write()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's actions (once, for all config entries)."""
    hass.services.async_register(DOMAIN, "start_charging", _async_start, schema=START_SCHEMA)
    hass.services.async_register(
        DOMAIN, "cancel_reservation", _async_cancel, schema=CANCEL_SCHEMA
    )
    hass.services.async_register(DOMAIN, "set_boost", _async_boost, schema=BOOST_SCHEMA)
