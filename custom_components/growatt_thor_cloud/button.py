"""Buttons to send the staged schedule for the Growatt THOR integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .charge_mode import MODE_FAST
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity
from .schedule import async_cancel_reservations, async_start, ha_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: start the staged schedule, cancel reservations."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []
    for sn in coordinator.data:
        entities.extend((ThorStartPlanButton(coordinator, sn), ThorCancelButton(coordinator, sn)))
    async_add_entities(entities)


class ThorStartPlanButton(ThorEntity, ButtonEntity):
    """Fast: start now or reserve a start, with the staged limit."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "start_plan")

    @property
    def available(self) -> bool:
        # Starts with a limit exist in Fast only.
        return super().available and self.charger.charge_mode.get("mode") == MODE_FAST

    async def async_press(self) -> None:
        with ha_errors("Could not start charging"):
            await async_start(self.coordinator, self._sn, self.coordinator.plan(self._sn))
        await self.coordinator.async_request_refresh()


class ThorCancelButton(ThorEntity, ButtonEntity):
    """Cancel the charger's reservations; only available when there are some."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "cancel_reservation")

    @property
    def available(self) -> bool:
        return super().available and bool(self.charger.reservations)

    async def async_press(self) -> None:
        with ha_errors("Could not cancel the reservation"):
            await async_cancel_reservations(self.coordinator, self._sn)
        await self.coordinator.async_request_refresh()
