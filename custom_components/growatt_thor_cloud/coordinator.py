"""Data update coordinator for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GrowattThorApi, GrowattThorApiError, GrowattThorAuthError
from .clock import charger_offset, format_offset, time_zone
from .const import (
    ACTIVE_STATES,
    BACKOFF_INTERVALS,
    CONF_SCAN_INTERVAL,
    CONFIG_REFRESH_INTERVAL,
    CONNECTOR_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RESERVATION_STATES,
    SESSION_STATES,
    STALE_DATA_GRACE,
)

_LOGGER = logging.getLogger(__name__)

TIME_ZONE_HELP_URL = "https://github.com/fabioscarparo/ha-growatt-thor-cloud#time-zone"
# Sessions read from the history: two, in case the newest one has not ended yet.
SESSIONS_READ = 2
# A write is confirmed by the charger about a minute later: read the settings again then.
CONFIRM_DELAY = timedelta(seconds=90)

type GrowattThorConfigEntry = ConfigEntry[GrowattThorCoordinator]


def clock_issue_id(sn: str) -> str:
    """Repairs issue raised while a charger's clock is off."""
    return f"time_zone_{sn}"


@dataclass
class ThorCharger:
    """Snapshot of one charger, one raw API payload per endpoint."""

    sn: str
    summary: dict[str, Any]  # /ocpp/api/list entry
    config: dict[str, Any] = field(default_factory=dict)  # /ocpp/api/configInfo
    connector: dict[str, Any] = field(default_factory=dict)  # /ocpp/charge/info
    reservations: list[dict[str, Any]] = field(default_factory=list)  # /ocpp/api/ReserveNow
    charge_mode: dict[str, Any] = field(default_factory=dict)  # /ocpp/chargeMode
    # Newest ended session of /ocpp/api/chargeRecord; the live data resets after a session.
    last_session: dict[str, Any] = field(default_factory=dict)

    @property
    def price_conf(self) -> list[dict[str, Any]]:
        """Tariff time slots set by the user: [{"time": "HH:MM-HH:MM", "price": "0.21"}]."""
        return self.config.get("priceConf") or self.summary.get("priceConf") or []

    @property
    def rated_power_kw(self) -> float | None:
        """Charger rating in kW (config "power" is in W, e.g. 7000 for a THOR 07AS)."""
        try:
            return float(self.config["power"]) / 1000
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def shared(self) -> bool:
        """Shared with this account by its owner: settings and modes stay read-only."""
        return str(self.summary.get("type")) == "1"

    @property
    def rfid_only(self) -> bool:
        """RFID authorization: sessions start and stop with a card, not remotely."""
        return str(self.config.get("G_ChargerMode")) == "2"

    @property
    def in_session(self) -> bool:
        """A session is open or closing (see SESSION_STATES)."""
        return self.connector.get("status") in SESSION_STATES

    def supports(self, feature: str) -> bool:
        """A feature flag of the settings (isSupport...); a missing flag means supported."""
        value = self.config.get(feature)
        return value is None or str(value).lower() in ("true", "1")


@dataclass
class ChargePlan:
    """Values staged in HA for the next scheduled start, Boost and grid import.

    The charger only learns them when a start is requested or Boost or grid
    import is turned on; until then they live here (and in the entities'
    restored state).
    None means "not set yet": the charger keeps no such values, so none are
    invented; using an unset value is reported as an error.
    """

    limit: str = "none"  # none / cost / energy / duration
    limit_cost: float | None = None  # currency
    limit_energy: float | None = None  # kWh
    limit_duration: int | None = None  # minutes
    start: str = "now"  # now / at_time / every_day
    start_time: time | None = None
    boost_type: str = "manual"  # manual / smart
    boost_from: time | None = None  # manual: full power in this window
    boost_to: time | None = None
    boost_departure: time | None = None  # smart: energy guaranteed by this time
    boost_energy: float | None = None  # smart: kWh
    # PV Linkage: grid power topping up the surplus while grid import is on, kW.
    import_grid: float | None = None
    # Off-peak slots; a slot whose start equals its end is unused ("00:00-00:00").
    off_peak_1_from: time = time(0, 0)
    off_peak_1_to: time = time(0, 0)
    off_peak_2_from: time = time(0, 0)
    off_peak_2_to: time = time(0, 0)
    off_peak_3_from: time = time(0, 0)
    off_peak_3_to: time = time(0, 0)
    # Slots beyond the third, set outside HA ("HH:MM-HH:MM"), kept as they are.
    off_peak_extra: list[str] = field(default_factory=list)
    # True once the user staged slots in HA; until then they follow the charger.
    off_peak_staged: bool = False


class GrowattThorCoordinator(DataUpdateCoordinator[dict[str, ThorCharger]]):
    """Polls every charger on the account; data is keyed by serial number.

    Growatt rate-limits its cloud, so polling is gentle: settings are read
    every few minutes, failures slow polling down, and the last data is kept
    for a while before entities turn unavailable.
    """

    config_entry: GrowattThorConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: GrowattThorConfigEntry, api: GrowattThorApi
    ) -> None:
        interval = timedelta(
            seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=interval,
        )
        self.api = api
        self.plans: dict[str, ChargePlan] = {}
        self._base_interval = interval
        self._failures = 0
        self._last_success: datetime | None = None
        self._config_fetched_at: datetime | None = None
        self._config_stale = True
        # When to read the settings again after a write, once the charger has confirmed it.
        self._confirm_at: datetime | None = None

    @property
    def base_interval(self) -> timedelta:
        """Polling interval from the options, before any back-off."""
        return self._base_interval

    def plan(self, sn: str) -> ChargePlan:
        """Staged schedule and Boost values for a charger."""
        return self.plans.setdefault(sn, ChargePlan())

    async def async_refresh_after_write(self) -> None:
        """Refresh soon, re-reading settings and reservations, to confirm a change.

        The charger applies and confirms new settings about a minute later, so
        they are read once more on the first poll after CONFIRM_DELAY.
        """
        self._config_stale = True
        self._confirm_at = dt_util.utcnow() + CONFIRM_DELAY
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, ThorCharger]:
        try:
            chargers = await self._async_fetch()
        except GrowattThorAuthError as err:
            # Starts the reauth flow and stops polling with bad credentials.
            raise ConfigEntryAuthFailed(str(err)) from err
        except GrowattThorApiError as err:
            self._failures += 1
            step = BACKOFF_INTERVALS[min(self._failures, len(BACKOFF_INTERVALS)) - 1]
            self.update_interval = max(self._base_interval, timedelta(seconds=step))
            retry = int(self.update_interval.total_seconds())
            if (
                self.data
                and self._last_success
                and dt_util.utcnow() - self._last_success < STALE_DATA_GRACE
            ):
                # Brief outage or rate limit: keep entities on the last values.
                _LOGGER.warning("Growatt cloud error, keeping last data, retry in %s s: %s", retry, err)
                return self.data
            raise UpdateFailed(f"{err} (retry in {retry} s)") from err
        self._failures = 0
        self.update_interval = self._base_interval
        self._last_success = dt_util.utcnow()
        self._check_clocks(chargers)
        return chargers

    def _check_clocks(self, chargers: dict[str, ThorCharger]) -> None:
        """Warn in Repairs while a charger's clock differs from Home Assistant's.

        Compared at noon, away from the hour daylight saving changes; on the
        charger's own switch days the warning is left as it is.
        """
        noon = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
        ha_offset = noon.utcoffset()
        for sn, charger in chargers.items():
            offset = charger_offset(charger.config, noon.date())
            if offset is None or ha_offset is None:
                continue
            issue_id = clock_issue_id(sn)
            if offset == ha_offset:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                continue
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                learn_more_url=TIME_ZONE_HELP_URL,
                translation_key="time_zone_mismatch",
                translation_placeholders={
                    "name": charger.summary.get("name") or sn,
                    "zone": time_zone(charger.config) or "",
                    "charger_offset": format_offset(offset),
                    "ha_offset": format_offset(ha_offset),
                },
            )

    async def _async_fetch(self) -> dict[str, ThorCharger]:
        # Sequential on purpose, to keep the load on Growatt's cloud low.
        now = dt_util.utcnow()
        confirm_due = self._confirm_at is not None and now >= self._confirm_at
        refresh_config = (
            self._config_stale
            or confirm_due
            or self._config_fetched_at is None
            or now - self._config_fetched_at >= CONFIG_REFRESH_INTERVAL
        )
        chargers: dict[str, ThorCharger] = {}
        for summary in await self.api.async_get_chargers():
            sn = summary.get("chargeId")
            if not sn:
                continue  # Malformed entry: nothing to address it by.
            previous = (self.data or {}).get(sn)
            if refresh_config or previous is None:
                config = await self.api.async_get_config(sn)
            else:
                config = previous.config
            connector = await self.api.async_get_connector(sn, CONNECTOR_ID)
            reservations = previous.reservations if previous else []
            # Reservations have their own request: read them while one is pending
            # or listed (to see it go), and with the settings otherwise.
            if (
                refresh_config
                or previous is None
                or previous.reservations
                or connector.get("status") in RESERVATION_STATES
            ):
                try:
                    reservations = await self.api.async_get_reservations(sn, CONNECTOR_ID)
                except GrowattThorApiError as err:
                    # Secondary data: keep the last list instead of failing the update.
                    _LOGGER.debug("Reservation list not available for %s: %s", sn, err)
            last_session = previous.last_session if previous else {}
            # The history only changes when a session ends: read it with the settings,
            # and right after a transaction stops.
            ended = (
                previous is not None
                and previous.connector.get("status") in ACTIVE_STATES
                and connector.get("status") not in ACTIVE_STATES
            )
            if refresh_config or previous is None or ended:
                try:
                    sessions = await self.api.async_get_sessions(sn, SESSIONS_READ)
                except GrowattThorApiError as err:
                    # Secondary data, like the reservations.
                    _LOGGER.debug("Charge history not available for %s: %s", sn, err)
                else:
                    last_session = next(
                        (s for s in sessions if s.get("sysEndTime") or s.get("endtime")),
                        last_session,
                    )
            chargers[sn] = ThorCharger(
                sn=sn,
                summary=summary,
                config=config,
                connector=connector,
                reservations=reservations,
                charge_mode=await self.api.async_get_charge_mode(sn, CONNECTOR_ID),
                last_session=last_session,
            )
        if refresh_config:
            self._config_fetched_at = now
            self._config_stale = False
        if confirm_due:
            self._confirm_at = None
        return chargers
