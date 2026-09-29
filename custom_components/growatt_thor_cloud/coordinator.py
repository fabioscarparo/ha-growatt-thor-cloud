"""Data update coordinator for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GrowattThorApi, GrowattThorApiError, GrowattThorAuthError
from .const import CONNECTOR_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type GrowattThorConfigEntry = ConfigEntry[GrowattThorCoordinator]


@dataclass
class ThorCharger:
    """Snapshot of one charger, one raw API payload per endpoint."""

    sn: str
    summary: dict[str, Any]  # /ocpp/api/list entry
    config: dict[str, Any] = field(default_factory=dict)  # /ocpp/api/configInfo
    connector: dict[str, Any] = field(default_factory=dict)  # /ocpp/charge/info
    charge_mode: dict[str, Any] = field(default_factory=dict)  # /ocpp/chargeMode


class GrowattThorCoordinator(DataUpdateCoordinator[dict[str, ThorCharger]]):
    """Polls every charger on the account; data is keyed by serial number."""

    config_entry: GrowattThorConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: GrowattThorConfigEntry, api: GrowattThorApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, ThorCharger]:
        # Sequential on purpose: four small requests per charger per minute keep the
        # load on Growatt's cloud low.
        try:
            chargers: dict[str, ThorCharger] = {}
            for summary in await self.api.async_get_chargers():
                sn = summary["chargeId"]
                chargers[sn] = ThorCharger(
                    sn=sn,
                    summary=summary,
                    config=await self.api.async_get_config(sn),
                    connector=await self.api.async_get_connector(sn, CONNECTOR_ID),
                    charge_mode=await self.api.async_get_charge_mode(sn, CONNECTOR_ID),
                )
        except GrowattThorAuthError as err:
            # Starts the reauth flow instead of retrying with bad credentials.
            raise ConfigEntryAuthFailed(str(err)) from err
        except GrowattThorApiError as err:
            raise UpdateFailed(str(err)) from err
        return chargers
