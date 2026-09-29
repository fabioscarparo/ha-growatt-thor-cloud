"""Base entity for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.restore_state import ExtraStoredData
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GrowattThorCoordinator, ThorCharger


class ThorEntity(CoordinatorEntity[GrowattThorCoordinator]):
    """Entity bound to one charger (device), identified by its serial number."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GrowattThorCoordinator, sn: str, key: str) -> None:
        super().__init__(coordinator)
        self._sn = sn
        self._attr_unique_id = f"{sn}_{key}"
        # The same key names the entity through translations/<lang>.json.
        self._attr_translation_key = key
        charger = coordinator.data[sn]
        config = charger.config
        mac = config.get("mac")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            # The MAC lets HA merge this device with ones found by other integrations.
            connections={(CONNECTION_NETWORK_MAC, mac)} if mac else set(),
            name=charger.summary.get("name") or sn,
            manufacturer=charger.summary.get("vendor") or "Growatt",
            model=config.get("deviceModel") or config.get("model"),
            sw_version=config.get("version"),
            serial_number=sn,
        )

    @property
    def charger(self) -> ThorCharger:
        """Latest snapshot of this entity's charger."""
        return self.coordinator.data[self._sn]

    @property
    def available(self) -> bool:
        # A charger removed from the account disappears from the next poll.
        return super().available and self._sn in self.coordinator.data


def to_float(value: object) -> float | None:
    """Parse numbers the API returns as int, float or string; None if not numeric."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


@dataclass
class PlanStoredData(ExtraStoredData):
    """A staged plan value as saved across restarts (None = never set).

    Stored under its own key: values saved by older versions, which invented
    defaults, lack it and are ignored instead of coming back.
    """

    value: str | None

    def as_dict(self) -> dict[str, Any]:
        return {"plan_value": self.value}

    @classmethod
    def restore(cls, extra: ExtraStoredData | None) -> str | None:
        """The saved value, or None if unset or saved by an older version."""
        if extra is None:
            return None
        return extra.as_dict().get("plan_value")
