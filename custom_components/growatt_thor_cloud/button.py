"""Buttons for the Growatt THOR integration: staged start, cancel and unlock."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .charge_mode import MODE_FAST
from .const import CONNECTOR_ID, UNLOCK_STATES
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity
from .schedule import async_cancel_reservations, async_start, ha_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: start the staged schedule, cancel reservations, unlock."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []
    for sn in coordinator.data:
        entities.extend(
            (
                ThorStartPlanButton(coordinator, sn),
                ThorCancelButton(coordinator, sn),
                ThorUnlockButton(coordinator, sn),
            )
        )
    async_add_entities(entities)


class ThorStartPlanButton(ThorEntity, ButtonEntity):
    """Fast: start now or reserve a start, with the staged limit."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "start_plan")

    @property
    def available(self) -> bool:
        # Starts with a limit exist in Fast only, and wait for the open session to end.
        return (
            super().available
            and self.charger.charge_mode.get("mode") == MODE_FAST
            and not self.charger.in_session
        )

    async def async_press(self) -> None:
        with ha_errors("Could not start charging"):
            await async_start(self.coordinator, self._sn, self.coordinator.plan(self._sn))
        # Also re-reads the reservations, which a timed start creates.
        await self.coordinator.async_refresh_after_write()


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
        await self.coordinator.async_refresh_after_write()


class ThorUnlockButton(ThorEntity, ButtonEntity):
    """Unlock the cable at the charger; available while no charge is in progress."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "unlock")

    @property
    def available(self) -> bool:
        return super().available and self.charger.connector.get("status") in UNLOCK_STATES

    async def async_press(self) -> None:
        try:
            await self.coordinator.api.async_unlock(self._sn, CONNECTOR_ID)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not unlock the connector: {err}") from err
        # The lock state comes with the connector data: refresh to pick it up.
        await self.coordinator.async_request_refresh()
