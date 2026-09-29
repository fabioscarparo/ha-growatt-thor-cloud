"""Sensors for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .coordinator import GrowattThorConfigEntry, ThorCharger
from .entity import ThorEntity, to_float
from .schedule import LIMIT_TYPES, next_reservation

# OCPP StatusNotification values -> HA enum states (snake_case for translations).
CONNECTOR_STATUS = {
    "Available": "available",
    "Preparing": "preparing",
    "Charging": "charging",
    "SuspendedEV": "suspended_ev",
    "SuspendedEVSE": "suspended_evse",
    "Finishing": "finishing",
    "Reserved": "reserved",
    "Unavailable": "unavailable",
    "Faulted": "faulted",
}

# G_ExternalSamplingCurWring -> how the charger measures the grid.
SAMPLING_DEVICES = {"0": "ct2000", "1": "meter", "2": "ct3000"}


def _in_slot(slot: str, now: str) -> bool:
    """Whether "HH:MM" `now` falls in an "HH:MM-HH:MM" slot (end included, may wrap midnight)."""
    start, _, end = slot.partition("-")
    if not start or not end:
        return False
    # Zero-padded times compare correctly as strings.
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def _tariff(charger: ThorCharger) -> float | None:
    """Price of the time slot in effect now.

    The configured tariff is a list of time slots (priceConf); the connector's
    "rate" is only the price applied to a running session and reads 0 when idle.
    """
    now = dt_util.now().strftime("%H:%M")
    for slot in charger.price_conf:
        if _in_slot(str(slot.get("time", "")), now):
            return to_float(slot.get("price"))
    return to_float(charger.connector.get("rate"))


def _power(charger: ThorCharger) -> float | None:
    """The API has no power field; derive it from V x I (valid for single-phase units)."""
    current = to_float(charger.connector.get("current"))
    voltage = to_float(charger.connector.get("voltage"))
    if current is None or voltage is None:
        return None
    return round(current * voltage, 1)


def _session_limit(charger: ThorCharger) -> str:
    """Limit of the current session: none / cost / energy / duration."""
    return LIMIT_TYPES.get(str(charger.connector.get("cKey") or ""), "none")


def _session_limit_attrs(charger: ThorCharger) -> dict[str, Any]:
    if _session_limit(charger) == "none":
        return {}
    return {"value": to_float(charger.connector.get("cValue"))}


def _next_reservation_attrs(charger: ThorCharger) -> dict[str, Any]:
    if (upcoming := next_reservation(charger)) is None:
        return {}
    reservation = upcoming[1]
    return {
        "every_day": str(reservation.get("loopType")) == "0",
        "limit": LIMIT_TYPES.get(str(reservation.get("cKey") or ""), "none"),
        "limit_value": to_float(reservation.get("cValue")),
    }


@dataclass(frozen=True, kw_only=True)
class ThorSensorDescription(SensorEntityDescription):
    """Sensor description with value and attribute getters over the charger snapshot."""

    value_fn: Callable[[ThorCharger], StateType | datetime]
    attrs_fn: Callable[[ThorCharger], dict[str, Any]] | None = None
    # When set, the unit is the charger currency (e.g. "EUR") plus this suffix.
    currency_unit: str | None = None


SENSORS: tuple[ThorSensorDescription, ...] = (
    ThorSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=list(CONNECTOR_STATUS.values()),
        value_fn=lambda c: CONNECTOR_STATUS.get(c.connector.get("status", "")),
    ),
    ThorSensorDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_power,
    ),
    ThorSensorDescription(
        key="current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda c: to_float(c.connector.get("current")),
    ),
    ThorSensorDescription(
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda c: to_float(c.connector.get("voltage")),
    ),
    # Resets to 0 at each session; TOTAL_INCREASING treats the drop as a new cycle,
    # so long-term statistics (and the Energy dashboard) keep adding up correctly.
    ThorSensorDescription(
        key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda c: to_float(c.connector.get("energy")),
    ),
    ThorSensorDescription(
        key="session_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda c: to_float(c.connector.get("ctime")),
    ),
    ThorSensorDescription(
        key="session_cost",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        currency_unit="",
        value_fn=lambda c: to_float(c.connector.get("cost")),
    ),
    ThorSensorDescription(
        key="tariff",
        currency_unit="/kWh",
        value_fn=_tariff,
    ),
    ThorSensorDescription(
        key="session_limit",
        device_class=SensorDeviceClass.ENUM,
        options=["none", *LIMIT_TYPES.values()],
        value_fn=_session_limit,
        attrs_fn=_session_limit_attrs,
    ),
    ThorSensorDescription(
        key="next_reservation",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c: upcoming[0] if (upcoming := next_reservation(c)) else None,
        attrs_fn=_next_reservation_attrs,
    ),
    ThorSensorDescription(
        key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.connector.get("errorCode") or None,
    ),
    ThorSensorDescription(
        key="vendor_error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.connector.get("vendorErrorCode") or None,
    ),
    # Grid measurement used by PV Linkage and load balancing: set up with the
    # installation, so read-only here.
    ThorSensorDescription(
        key="sampling_device",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=list(SAMPLING_DEVICES.values()),
        value_fn=lambda c: SAMPLING_DEVICES.get(str(c.config.get("G_ExternalSamplingCurWring"))),
    ),
    ThorSensorDescription(
        key="meter_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.config.get("G_PowerMeterType") or None,
    ),
    ThorSensorDescription(
        key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.config.get("ip") or None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """One set of sensors per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorSensor(coordinator, sn, description)
        for sn in coordinator.data
        for description in SENSORS
    )


class ThorSensor(ThorEntity, SensorEntity):
    """Sensor whose value comes from its description's value_fn."""

    entity_description: ThorSensorDescription

    def __init__(self, coordinator, sn: str, description: ThorSensorDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.charger)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.charger)

    @property
    def native_unit_of_measurement(self) -> str | None:
        # Monetary units follow the currency configured on the charger.
        suffix = self.entity_description.currency_unit
        if suffix is None:
            return super().native_unit_of_measurement
        currency = self.charger.config.get("unit") or self.charger.summary.get("unit")
        return f"{currency}{suffix}" if currency else None
