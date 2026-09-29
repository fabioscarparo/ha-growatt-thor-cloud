"""Numeric settings for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .charge_mode import MODE_PV_LINKAGE, charge_mode_fields, format_kw
from .const import CONNECTOR_ID
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity, to_float
from .schedule import async_update_plan, effective_plan, ha_errors

# Upper bound for power settings when the charger does not report its rating.
DEFAULT_MAX_POWER_KW = 22.0


@dataclass(frozen=True, kw_only=True)
class ThorNumberDescription(NumberEntityDescription):
    """A numeric charger setting; leave native_max_value unset to use the rated power."""

    config_key: str
    to_api: Callable[[float], Any]  # Converts HA's float to the setting's wire format.


NUMBERS: tuple[ThorNumberDescription, ...] = (
    ThorNumberDescription(
        key="max_current",
        device_class=NumberDeviceClass.CURRENT,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,  # IEC 61851 minimum; the API accepts down to 3.
        native_max_value=32,
        native_step=1,
        mode=NumberMode.SLIDER,
        config_key="G_MaxCurrent",
        to_api=lambda v: str(int(v)),  # Sent as a string.
    ),
    # Low-level grid import used by the ECO solar mode (manual, parameter 21).
    # Hidden by default: the PV Linkage grid import below is the everyday control.
    ThorNumberDescription(
        key="solar_limit_power",
        device_class=NumberDeviceClass.POWER,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        native_min_value=0,
        native_step=0.01,
        mode=NumberMode.BOX,
        config_key="G_SolarLimitPower",
        to_api=lambda v: round(v, 2),
    ),
)


@dataclass(frozen=True, kw_only=True)
class ThorPlanNumberDescription(NumberEntityDescription):
    """A value staged in HA for the next scheduled start or for Boost."""

    plan_field: str
    currency: bool = False  # Unit is the charger currency.
    boost: bool = False  # Resent at once when changed while Boost runs.


PLAN_NUMBERS: tuple[ThorPlanNumberDescription, ...] = (
    ThorPlanNumberDescription(
        key="limit_cost",
        plan_field="limit_cost",
        native_min_value=0.5,
        native_max_value=500,
        native_step=0.5,
        mode=NumberMode.BOX,
        currency=True,
    ),
    ThorPlanNumberDescription(
        key="limit_energy",
        plan_field="limit_energy",
        device_class=NumberDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        native_min_value=0.5,
        native_max_value=200,
        native_step=0.5,
        mode=NumberMode.BOX,
    ),
    ThorPlanNumberDescription(
        key="limit_duration",
        plan_field="limit_duration",
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=1,
        native_max_value=24 * 60 - 1,  # The app's picker stops at 23 h 59 min.
        native_step=1,
        mode=NumberMode.BOX,
    ),
    ThorPlanNumberDescription(
        key="boost_energy",
        plan_field="boost_energy",
        device_class=NumberDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        native_min_value=0.5,
        native_max_value=200,
        native_step=0.5,
        mode=NumberMode.BOX,
        boost=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: numeric settings, the PV Linkage grid import and staged plan values."""
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = []
    for sn in coordinator.data:
        entities.extend(ThorNumber(coordinator, sn, description) for description in NUMBERS)
        entities.append(ThorImportGridNumber(coordinator, sn))
        entities.extend(
            ThorPlanNumber(coordinator, sn, description) for description in PLAN_NUMBERS
        )
    async_add_entities(entities)


class ThorNumber(ThorEntity, NumberEntity):
    """Number backed by a single charger setting."""

    entity_description: ThorNumberDescription

    def __init__(self, coordinator, sn: str, description: ThorNumberDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description
        if description.native_max_value is None:
            self._attr_native_max_value = self.charger.rated_power_kw or DEFAULT_MAX_POWER_KW

    @property
    def native_value(self) -> float | None:
        return to_float(self.charger.config.get(self.entity_description.config_key))

    async def async_set_native_value(self, value: float) -> None:
        """Write the setting, show it right away, then confirm with a refresh."""
        key = self.entity_description.config_key
        api_value = self.entity_description.to_api(value)
        try:
            await self.coordinator.api.async_set_config(self._sn, key, api_value)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not set {key}: {err}") from err
        self.charger.config[key] = api_value
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()


class ThorImportGridNumber(ThorEntity, NumberEntity):
    """Grid power allowed to top up PV surplus in PV Linkage (0 = surplus only).

    With 0 kW charging pauses when surplus drops below the 1.4 kW minimum
    (4.1 kW three-phase); with P kW the grid supplies up to P to keep charging.
    """

    _attr_device_class = NumberDeviceClass.POWER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_native_min_value = 0
    _attr_native_step = 0.1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "import_grid_power")
        self._attr_native_max_value = self.charger.rated_power_kw or DEFAULT_MAX_POWER_KW

    @property
    def available(self) -> bool:
        # Only meaningful while in PV Linkage.
        return super().available and self.charger.charge_mode.get("mode") == MODE_PV_LINKAGE

    @property
    def native_value(self) -> float | None:
        return to_float(self.charger.charge_mode.get("importGrid"))

    async def async_set_native_value(self, value: float) -> None:
        """Resend the PV Linkage mode object with the new grid import."""
        fields = charge_mode_fields(self.charger, MODE_PV_LINKAGE, importGrid=format_kw(value))
        try:
            await self.coordinator.api.async_set_charge_mode(self._sn, CONNECTOR_ID, fields)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not set grid import: {err}") from err
        self.charger.charge_mode.update(fields)
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()


class ThorPlanNumber(ThorEntity, RestoreNumber):
    """Number for a staged plan value; the value survives restarts."""

    entity_description: ThorPlanNumberDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, sn: str, description: ThorPlanNumberDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last and last.native_value is not None:
            field = self.entity_description.plan_field
            plan = self.coordinator.plan(self._sn)
            setattr(plan, field, type(getattr(plan, field))(last.native_value))

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.entity_description.currency:
            return self.charger.config.get("unit") or self.charger.summary.get("unit")
        return super().native_unit_of_measurement

    @property
    def native_value(self) -> float:
        return getattr(
            effective_plan(self.coordinator, self._sn), self.entity_description.plan_field
        )

    async def async_set_native_value(self, value: float) -> None:
        field = self.entity_description.plan_field
        # Keep the field's type: durations are whole minutes.
        value = type(getattr(self.coordinator.plan(self._sn), field))(value)
        with ha_errors("Could not update Boost"):
            await async_update_plan(
                self.coordinator, self._sn, field, value, self.entity_description.boost
            )
