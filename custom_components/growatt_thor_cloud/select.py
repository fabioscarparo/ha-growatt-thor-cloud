"""Selects for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .api import GrowattThorError
from .charge_mode import MODE_FAST, MODE_OFF_PEAK, MODE_PV_LINKAGE, charge_mode_fields
from .const import CONNECTOR_ID
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity
from .schedule import (
    LIVE_BOOST,
    async_update_plan,
    effective_plan,
    ha_errors,
    off_peak_fields,
)

# HA option -> /ocpp/chargeMode "mode" value.
CHARGE_MODES = {
    "fast": MODE_FAST,
    "pv_linkage": MODE_PV_LINKAGE,
    "off_peak": MODE_OFF_PEAK,
}


@dataclass(frozen=True, kw_only=True)
class ThorSelectDescription(SelectEntityDescription):
    """An enumerated charger setting; options are the keys of `values`."""

    config_key: str
    values: dict[str, int]  # HA option -> integer code used by the API.


SELECTS: tuple[ThorSelectDescription, ...] = (
    # Low-level solar setting behind the charge modes (manual, parameter 21):
    # FAST = no PV, ECO = PV surplus + grid import, ECO+ = PV surplus only.
    # Hidden by default: the charge mode select is the everyday control.
    ThorSelectDescription(
        key="solar_mode",
        config_key="G_SolarMode",
        values={"fast": 0, "eco": 1, "eco_plus": 2},
        entity_registry_enabled_default=False,
    ),
    # How a session is authorized (manual, parameter 26).
    ThorSelectDescription(
        key="authorization_mode",
        config_key="G_ChargerMode",
        values={"app": 1, "rfid": 2, "plug_and_charge": 3},
    ),
)


@dataclass(frozen=True, kw_only=True)
class ThorPlanSelectDescription(SelectEntityDescription):
    """A choice staged in HA for the next scheduled start or for Boost."""

    plan_field: str
    live: str | None = None  # Live setting it belongs to (resent while in use).


PLAN_SELECTS: tuple[ThorPlanSelectDescription, ...] = (
    ThorPlanSelectDescription(
        key="charge_limit",
        plan_field="limit",
        options=["none", "cost", "energy", "duration"],
    ),
    ThorPlanSelectDescription(
        key="start_mode",
        plan_field="start",
        options=["now", "at_time", "every_day"],
    ),
    ThorPlanSelectDescription(
        key="boost_type",
        plan_field="boost_type",
        options=["manual", "smart"],
        live=LIVE_BOOST,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: charge mode, enumerated settings and staged plan choices."""
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = []
    for sn in coordinator.data:
        entities.append(ThorChargeModeSelect(coordinator, sn))
        entities.extend(
            ThorSelect(coordinator, sn, description) for description in SELECTS
        )
        entities.extend(
            ThorPlanSelect(coordinator, sn, description) for description in PLAN_SELECTS
        )
    async_add_entities(entities)


class ThorChargeModeSelect(ThorEntity, SelectEntity):
    """Fast / PV Linkage / Off-peak, the charger's everyday working mode."""

    _attr_options = list(CHARGE_MODES)

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "charge_mode")

    @property
    def current_option(self) -> str | None:
        mode = self.charger.charge_mode.get("mode")
        return next((opt for opt, m in CHARGE_MODES.items() if m == mode), None)

    async def async_select_option(self, option: str) -> None:
        mode = CHARGE_MODES[option]
        with ha_errors("Could not set charge mode"):
            if mode == MODE_OFF_PEAK:
                # Off-peak goes with the staged slots (Off-peak - Slot n entities).
                plan = effective_plan(self.coordinator, self._sn)
                fields = off_peak_fields(self.charger, plan)
            else:
                fields = charge_mode_fields(self.charger, mode)
            await self.coordinator.api.async_set_charge_mode(self._sn, CONNECTOR_ID, fields)
        self.charger.charge_mode.update(fields)
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()


class ThorSelect(ThorEntity, SelectEntity):
    """Select backed by a single integer-coded charger setting."""

    entity_description: ThorSelectDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, sn: str, description: ThorSelectDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description
        self._attr_options = list(description.values)

    @property
    def current_option(self) -> str | None:
        # The API returns these codes as int or string ("3"); unknown codes read as None.
        raw = self.charger.config.get(self.entity_description.config_key)
        try:
            value = int(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return next(
            (opt for opt, v in self.entity_description.values.items() if v == value), None
        )

    async def async_select_option(self, option: str) -> None:
        """Write the setting, show it right away, then confirm with a refresh."""
        key = self.entity_description.config_key
        value = self.entity_description.values[option]
        try:
            await self.coordinator.api.async_set_config(self._sn, key, value)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not set {key}: {err}") from err
        self.charger.config[key] = value
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()


class ThorPlanSelect(ThorEntity, SelectEntity, RestoreEntity):
    """Select for a staged plan value; the choice survives restarts."""

    entity_description: ThorPlanSelectDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator, sn: str, description: ThorPlanSelectDescription
    ) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self.options:
            setattr(self.coordinator.plan(self._sn), self.entity_description.plan_field, last.state)

    @property
    def current_option(self) -> str | None:
        return getattr(
            effective_plan(self.coordinator, self._sn), self.entity_description.plan_field
        )

    async def async_select_option(self, option: str) -> None:
        with ha_errors("Could not update the setting"):
            await async_update_plan(
                self.coordinator,
                self._sn,
                self.entity_description.plan_field,
                option,
                self.entity_description.live,
            )
