"""Config selects for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity


@dataclass(frozen=True, kw_only=True)
class ThorSelectDescription(SelectEntityDescription):
    """An enumerated charger setting; options are the keys of `values`."""

    config_key: str
    values: dict[str, int]  # HA option -> integer code used by the API.


SELECTS: tuple[ThorSelectDescription, ...] = (
    # FAST = no PV, ECO = PV linkage, ECO+ = PV linkage+.
    ThorSelectDescription(
        key="solar_mode",
        config_key="G_SolarMode",
        values={"fast": 0, "eco": 1, "eco_plus": 2},
    ),
    # How a session is authorized: from the app, with an RFID card, or on plug-in.
    ThorSelectDescription(
        key="authorization_mode",
        config_key="G_ChargerMode",
        values={"app": 1, "rfid": 2, "plug_and_charge": 3},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """One set of selects per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorSelect(coordinator, sn, description)
        for sn in coordinator.data
        for description in SELECTS
    )


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
        await self.coordinator.async_request_refresh()
