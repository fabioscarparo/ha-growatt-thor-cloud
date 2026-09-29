"""Binary sensors for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONNECTOR_STATUS
from .coordinator import GrowattThorConfigEntry, ThorCharger
from .entity import ThorEntity


def _online(charger: ThorCharger) -> bool | None:
    """Whether the charger is reachable, judged from its status.

    "Unavailable" and statuses outside the known set mean it is not. The
    payload's "online" flag is ignored: its meaning is unverified.
    """
    status = charger.connector.get("status")
    if not status or status == "None":  # Still loading.
        return None
    return status in CONNECTOR_STATUS and status != "Unavailable"


def _unlocked(charger: ThorCharger) -> bool | None:
    """HA's LOCK class reads on = unlocked, matching elockstate == "unlocked"."""
    state = charger.connector.get("elockstate") or charger.config.get("elockstate")
    return None if not state else state == "unlocked"


@dataclass(frozen=True, kw_only=True)
class ThorBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with a state getter over the charger snapshot."""

    value_fn: Callable[[ThorCharger], bool | None]


BINARY_SENSORS: tuple[ThorBinarySensorDescription, ...] = (
    ThorBinarySensorDescription(
        key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_online,
    ),
    ThorBinarySensorDescription(
        key="cable_lock",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=_unlocked,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """One set of binary sensors per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorBinarySensor(coordinator, sn, description)
        for sn in coordinator.data
        for description in BINARY_SENSORS
    )


class ThorBinarySensor(ThorEntity, BinarySensorEntity):
    """Binary sensor whose state comes from its description's value_fn."""

    entity_description: ThorBinarySensorDescription

    def __init__(
        self, coordinator, sn: str, description: ThorBinarySensorDescription
    ) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.charger)
