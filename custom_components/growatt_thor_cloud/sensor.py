"""Sensors for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .clock import charger_offset, dst_period, time_zone
from .const import ACTIVE_STATES, CONNECTOR_STATUS, SESSION_STATES
from .coordinator import GrowattThorConfigEntry, ThorCharger
from .entity import ThorEntity, to_float
from .schedule import LIMIT_TYPES, boost_params, is_boost_on, next_reservation

# G_ExternalSamplingCurWring -> how the charger measures the grid.
SAMPLING_DEVICES = {"0": "ct2000", "1": "meter", "2": "ct3000"}
# Session limit type -> connector field measured against it.
LIMIT_PROGRESS = {"cost": "cost", "energy": "energy", "duration": "ctime"}
NETWORK_CONNECTIONS = ["wifi", "cable"]  # G_NetType
NETWORK_MODES = ["dhcp", "static"]  # G_NetworkMode
# G_WorkingMode, the mode the charger runs: in PV Linkage, "PVlink" may draw on
# the grid import allowance, "PVlink+" uses the surplus only.
WORKING_MODES = {
    "fast": "fast",
    "pvlink": "pv_linkage_grid",
    "pvlink+": "pv_linkage_surplus",
    "off peak": "off_peak",
    "power distribution": "power_distribution",
}
# A running Boost is reported as a suffix, e.g. "PVlink ManualBoost".
BOOST_SUFFIXES = ("manualboost", "smartboost")


def _option(value: object, options: list[str]) -> str | None:
    """A setting matched case-insensitively against enum options; None if unknown."""
    text = str(value or "").lower()
    return text if text in options else None


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
    "rate" is only the price applied to a running session and reads 0 when idle,
    so it is used only during a session when no slot covers the current time.
    """
    now = dt_util.now().strftime("%H:%M")
    for slot in charger.price_conf:
        if _in_slot(str(slot.get("time", "")), now):
            return to_float(slot.get("price"))
    if charger.connector.get("status") in ACTIVE_STATES:
        return to_float(charger.connector.get("rate"))
    return None


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


def _progress(charger: ThorCharger) -> float | None:
    """Share of the session's target reached, in %.

    The target is the session limit (Fast) or the smart Boost energy; unknown
    outside a session and without a target.
    """
    connector = charger.connector
    if connector.get("status") not in ACTIVE_STATES:
        return None
    limit = LIMIT_TYPES.get(str(connector.get("cKey") or ""))
    if limit:
        target = to_float(connector.get("cValue"))
        done = to_float(connector.get(LIMIT_PROGRESS[limit]))
    elif is_boost_on(charger):
        # Only smart Boost has an energy; a manual window has no target.
        target = to_float(boost_params(charger).get("energy"))
        done = to_float(connector.get("energy"))
    else:
        return None
    if not target or done is None:
        return None
    return round(min(done / target * 100, 100.0), 1)


def _working_mode(charger: ThorCharger) -> str | None:
    """The charger's working mode, without its Boost suffix; None if not known."""
    raw = str(charger.config.get("G_WorkingMode") or "").strip().lower()
    for suffix in BOOST_SUFFIXES:
        raw = raw.removesuffix(suffix).strip()
    return WORKING_MODES.get(raw)


def _record_time(charger: ThorCharger, session: dict[str, Any], key: str) -> datetime | None:
    """A time of a history session, "YYYY-MM-DD HH:MM:SS" on the charger's clock.

    The epoch fields next to it (sysStartTime / sysEndTime) read that wall-clock
    time as UTC+8, so they are not used.
    """
    parsed = dt_util.parse_datetime(str(session.get(key) or ""))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        offset = charger_offset(charger.config, parsed.date())
        parsed = parsed.replace(
            tzinfo=dt_util.get_default_time_zone() if offset is None else timezone(offset)
        )
    return dt_util.as_utc(parsed)


def _session_time(charger: ThorCharger, key: str) -> datetime | None:
    """A time of the last session."""
    return _record_time(charger, charger.last_session, key)


def _today_energy(charger: ThorCharger) -> float:
    """Energy of today's sessions, kWh: those that ended today and the one open now.

    A session counts on the day it ends. Once it is in the history, the live value of
    the same transaction is not added again.
    """
    today = dt_util.now().date()
    total = 0.0
    recorded: set[str] = set()
    for session in charger.sessions:
        recorded.add(str(session.get("transactionId") or ""))
        end = _record_time(charger, session, "endtime")
        if end is not None and dt_util.as_local(end).date() == today:
            total += to_float(session.get("energy")) or 0.0
    connector = charger.connector
    transaction = str(connector.get("transactionId") or "")
    if (
        connector.get("status") in SESSION_STATES
        and transaction not in ("", "0")
        and transaction not in recorded
    ):
        total += to_float(connector.get("energy")) or 0.0
    return round(total, 3)


def _time_zone_attrs(charger: ThorCharger) -> dict[str, Any]:
    """Daylight saving start and end as "MM-DD", None when not set."""
    period = dst_period(charger.config)
    start, end = (f"{month:02d}-{day:02d}" for month, day in period) if period else (None, None)
    return {"daylight_saving_start": start, "daylight_saving_end": end}


def _meter_attrs(charger: ThorCharger) -> dict[str, Any]:
    """Bus address of the meter, when one is set up."""
    if not charger.config.get("G_PowerMeterType"):
        return {}
    return {"address": charger.config.get("G_PowerMeterAddr")}


def _next_reservation_attrs(charger: ThorCharger) -> dict[str, Any]:
    if (upcoming := next_reservation(charger)) is None:
        return {}
    reservation = upcoming[1]
    limit = LIMIT_TYPES.get(str(reservation.get("cKey") or ""), "none")
    return {
        "every_day": str(reservation.get("loopType")) == "0",
        "limit": limit,
        # cValue2 is the value to display; cValue is echoed back to cancel.
        "limit_value": (
            None
            if limit == "none"
            else to_float(reservation.get("cValue2", reservation.get("cValue")))
        ),
    }


@dataclass(frozen=True, kw_only=True)
class ThorSensorDescription(SensorEntityDescription):
    """Sensor description with value and attribute getters over the charger snapshot."""

    value_fn: Callable[[ThorCharger], StateType | datetime]
    attrs_fn: Callable[[ThorCharger], dict[str, Any]] | None = None
    # When set, the unit is the charger currency (e.g. "EUR") plus this suffix.
    currency_unit: str | None = None
    # For a total that starts again periodically: when the current period began.
    last_reset_fn: Callable[[], datetime] | None = None


SENSORS: tuple[ThorSensorDescription, ...] = (
    ThorSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=list(dict.fromkeys(CONNECTOR_STATUS.values())),  # "reserved" appears 3 times
        # Unknown values (including "None", still loading) read as unknown.
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
        key="session_progress",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=_progress,
    ),
    # The last ended session, from the charge history: the session sensors
    # above reset once a session is over.
    ThorSensorDescription(
        key="last_session",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c: _session_time(c, "endtime"),
    ),
    ThorSensorDescription(
        key="last_session_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c: _session_time(c, "starttime"),
    ),
    ThorSensorDescription(
        key="last_session_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda c: to_float(c.last_session.get("ctime")),
    ),
    ThorSensorDescription(
        key="last_session_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda c: to_float(c.last_session.get("energy")),
    ),
    ThorSensorDescription(
        key="last_session_cost",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        currency_unit="",
        value_fn=lambda c: to_float(c.last_session.get("cost")),
    ),
    # Starts again at midnight; it can dip slightly when a session moves from the
    # live data to the history, so it is a total and not an increasing one.
    ThorSensorDescription(
        key="today_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=_today_energy,
        last_reset_fn=dt_util.start_of_local_day,
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
        attrs_fn=_meter_attrs,
    ),
    ThorSensorDescription(
        key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.config.get("ip") or None,
    ),
    ThorSensorDescription(
        key="network_connection",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=NETWORK_CONNECTIONS,
        value_fn=lambda c: _option(c.config.get("G_NetType"), NETWORK_CONNECTIONS),
    ),
    ThorSensorDescription(
        key="network_mode",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=NETWORK_MODES,
        value_fn=lambda c: _option(c.config.get("G_NetworkMode"), NETWORK_MODES),
    ),
    # What the charger actually runs, as confirmed by it after a change.
    ThorSensorDescription(
        key="working_mode",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=list(WORKING_MODES.values()),
        value_fn=_working_mode,
    ),
    # The charger's clock; it must match Home Assistant's (see clock.py).
    ThorSensorDescription(
        key="time_zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: time_zone(c.config),
        attrs_fn=_time_zone_attrs,
    ),
    # Internal temperature at which the charger protects itself.
    ThorSensorDescription(
        key="protection_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: to_float(c.config.get("G_MaxTemperature")),
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
    def last_reset(self) -> datetime | None:
        last_reset_fn = self.entity_description.last_reset_fn
        return None if last_reset_fn is None else last_reset_fn()

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
