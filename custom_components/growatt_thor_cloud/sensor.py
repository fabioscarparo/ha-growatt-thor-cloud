"""Sensors for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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

from .coordinator import GrowattThorConfigEntry, ThorCharger
from .entity import ThorEntity, to_float

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
# /ocpp/chargeMode "mode" values -> HA enum states.
CHARGE_MODES = {"fast": "fast", "offPeak": "off_peak", "pvLinkage": "pv_linkage"}


def _power(charger: ThorCharger) -> float | None:
    """The API has no power field; derive it from V x I (valid for single-phase units)."""
    current = to_float(charger.connector.get("current"))
    voltage = to_float(charger.connector.get("voltage"))
    if current is None or voltage is None:
        return None
    return round(current * voltage, 1)


@dataclass(frozen=True, kw_only=True)
class ThorSensorDescription(SensorEntityDescription):
    """Sensor description with a value getter over the charger snapshot."""

    value_fn: Callable[[ThorCharger], StateType]
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
        key="charge_mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(CHARGE_MODES.values()),
        value_fn=lambda c: CHARGE_MODES.get(c.charge_mode.get("mode", "")),
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
    # "rate" is the configured price per kWh, not a power reading.
    ThorSensorDescription(
        key="tariff",
        currency_unit="/kWh",
        value_fn=lambda c: to_float(c.connector.get("rate")),
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
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.charger)

    @property
    def native_unit_of_measurement(self) -> str | None:
        # Monetary units follow the currency configured on the charger.
        suffix = self.entity_description.currency_unit
        if suffix is None:
            return super().native_unit_of_measurement
        currency = self.charger.config.get("unit") or self.charger.summary.get("unit")
        return f"{currency}{suffix}" if currency else None
