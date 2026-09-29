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
    # PV linkage threshold / grid import allowed in solar modes.
    ThorNumberDescription(
        key="solar_limit_power",
        device_class=NumberDeviceClass.POWER,
        entity_category=EntityCategory.CONFIG,
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
    """One set of numeric settings per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorNumber(coordinator, sn, description)
        for sn in coordinator.data
        for description in NUMBERS
    )


class ThorNumber(ThorEntity, NumberEntity):
    """Number backed by a single charger setting."""

    entity_description: ThorNumberDescription

    def __init__(self, coordinator, sn: str, description: ThorNumberDescription) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description
        if description.native_max_value is None:
            # Charger rating in W (e.g. 7000 for a THOR 07AS).
            rated = to_float(self.charger.config.get("power"))
            self._attr_native_max_value = rated / 1000 if rated else DEFAULT_MAX_POWER_KW

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
