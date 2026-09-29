"""Times staged for the next scheduled start and for Boost."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity
from .schedule import async_update_plan, effective_plan, ha_errors


@dataclass(frozen=True, kw_only=True)
class ThorPlanTimeDescription(TimeEntityDescription):
    """A time staged in HA."""

    plan_field: str
    boost: bool = False  # Resent at once when changed while Boost runs.


PLAN_TIMES: tuple[ThorPlanTimeDescription, ...] = (
    # Used when the start mode is "at time" or "every day".
    ThorPlanTimeDescription(key="start_time", plan_field="start_time"),
    # Manual Boost: full power from/to.
    ThorPlanTimeDescription(key="boost_from", plan_field="boost_from", boost=True),
    ThorPlanTimeDescription(key="boost_to", plan_field="boost_to", boost=True),
    # Smart Boost: energy guaranteed by this time.
    ThorPlanTimeDescription(key="boost_departure", plan_field="boost_departure", boost=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """One set of staged times per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorPlanTime(coordinator, sn, description)
        for sn in coordinator.data
        for description in PLAN_TIMES
    )


class ThorPlanTime(ThorEntity, TimeEntity, RestoreEntity):
    """Time for a staged plan value; the value survives restarts."""

    entity_description: ThorPlanTimeDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, sn: str, description: ThorPlanTimeDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None:
            return
        try:
            value = time.fromisoformat(last.state)
        except ValueError:
            return  # "unknown" / "unavailable"
        setattr(self.coordinator.plan(self._sn), self.entity_description.plan_field, value)

    @property
    def native_value(self) -> time:
        return getattr(
            effective_plan(self.coordinator, self._sn), self.entity_description.plan_field
        )

    async def async_set_value(self, value: time) -> None:
        with ha_errors("Could not update Boost"):
            await async_update_plan(
                self.coordinator,
                self._sn,
                self.entity_description.plan_field,
                value.replace(second=0, microsecond=0),
                self.entity_description.boost,
            )
