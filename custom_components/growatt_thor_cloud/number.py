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
)
from homeassistant.const import EntityCategory, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .charge_mode import MODE_PV_LINKAGE, charge_mode_fields, format_kw
from .const import CONNECTOR_ID
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity, to_float

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: one number per numeric setting plus the PV Linkage grid import."""
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = []
    for sn in coordinator.data:
        entities.extend(ThorNumber(coordinator, sn, description) for description in NUMBERS)
        entities.append(ThorImportGridNumber(coordinator, sn))
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
        await self.coordinator.async_request_refresh()


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
        await self.coordinator.async_request_refresh()
