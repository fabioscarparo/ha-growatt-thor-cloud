"""Switches for the Growatt THOR integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .const import ACTIVE_STATES, CONNECTOR_ID
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity
from .schedule import BOOST_MODES, async_set_boost, effective_plan, ha_errors, is_boost_on


@dataclass(frozen=True, kw_only=True)
class ThorConfigSwitchDescription(SwitchEntityDescription):
    """A charger setting exposed as a switch."""

    config_key: str
    on_value: Any  # Wire value meaning "on" (compared as string when reading).
    off_value: Any


CONFIG_SWITCHES: tuple[ThorConfigSwitchDescription, ...] = (
    # Dynamic load balancing against the external meter.
    ThorConfigSwitchDescription(
        key="load_balancing",
        entity_category=EntityCategory.CONFIG,
        config_key="G_ExternalLimitPowerEnable",
        on_value=1,
        off_value=0,
    ),
    # G_LCDCloseEnable turns on automatic screen-off, so "Disable" = display on.
    ThorConfigSwitchDescription(
        key="lcd_display",
        entity_category=EntityCategory.CONFIG,
        config_key="G_LCDCloseEnable",
        on_value="Disable",
        off_value="Enable",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: charging, Boost and one switch per boolean setting."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    for sn in coordinator.data:
        entities.append(ThorChargingSwitch(coordinator, sn))
        entities.append(ThorBoostSwitch(coordinator, sn))
        entities.extend(
            ThorConfigSwitch(coordinator, sn, description) for description in CONFIG_SWITCHES
        )
    async_add_entities(entities)


class ThorChargingSwitch(ThorEntity, SwitchEntity):
    """On while an OCPP transaction is running; toggling sends remote start/stop."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "charging")

    @property
    def is_on(self) -> bool:
        # Suspended states still hold an open transaction, so they count as on.
        return self.charger.connector.get("status") in ACTIVE_STATES

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.api.async_start_charging(self._sn, CONNECTOR_ID)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not start charging: {err}") from err
        # State follows the charger, not the command: refresh to pick up the result.
        await self.coordinator.async_refresh_after_write()

    async def async_turn_off(self, **kwargs: Any) -> None:
        # RemoteStopTransaction needs the id of the running transaction; 0 means none.
        transaction_id = str(self.charger.connector.get("transactionId") or "")
        if transaction_id in ("", "0"):
            raise HomeAssistantError("No charging session is running")
        try:
            await self.coordinator.api.async_stop_charging(
                self._sn, CONNECTOR_ID, transaction_id
            )
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not stop charging: {err}") from err
        await self.coordinator.async_refresh_after_write()


class ThorConfigSwitch(ThorEntity, SwitchEntity):
    """Switch backed by a single charger setting."""

    entity_description: ThorConfigSwitchDescription

    def __init__(
        self, coordinator, sn: str, description: ThorConfigSwitchDescription
    ) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        raw = self.charger.config.get(self.entity_description.config_key)
        if raw is None:
            return None
        # The API may return the same setting as int or string.
        return str(raw) == str(self.entity_description.on_value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(self.entity_description.on_value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(self.entity_description.off_value)

    async def _async_set(self, value: Any) -> None:
        """Write the setting, show it right away, then confirm with a refresh."""
        key = self.entity_description.config_key
        try:
            await self.coordinator.api.async_set_config(self._sn, key, value)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not set {key}: {err}") from err
        self.charger.config[key] = value
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()


class ThorBoostSwitch(ThorEntity, SwitchEntity):
    """Boost in PV Linkage / Off-peak, using the staged Boost type, window and energy."""

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "boost")

    @property
    def available(self) -> bool:
        return super().available and self.charger.charge_mode.get("mode") in BOOST_MODES

    @property
    def is_on(self) -> bool:
        return is_boost_on(self.charger)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, enabled: bool) -> None:
        with ha_errors("Could not set Boost"):
            await async_set_boost(
                self.coordinator, self._sn, effective_plan(self.coordinator, self._sn), enabled
            )
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()
