"""Switches for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .charge_mode import MODE_PV_LINKAGE
from .const import ACTIVE_STATES, CONNECTOR_ID, DOMAIN
from .coordinator import GrowattThorConfigEntry, ThorCharger
from .entity import ThorEntity, check_owner
from .schedule import (
    BOOST_MODES,
    async_set_boost,
    async_set_import_grid,
    check_remote_control,
    effective_plan,
    ha_errors,
    is_boost_on,
    is_import_grid_on,
)


@dataclass(frozen=True, kw_only=True)
class ThorConfigSwitchDescription(SwitchEntityDescription):
    """A charger setting exposed as a switch."""

    config_key: str
    on_value: Any  # Wire value meaning "on" (compared as text when reading).
    off_value: Any
    # When set, the switch is available only while this returns True.
    available_fn: Callable[[ThorCharger], bool] | None = None
    # When set, the switch is created only for chargers where this returns True.
    supported_fn: Callable[[ThorCharger], bool] | None = None


CONFIG_SWITCHES: tuple[ThorConfigSwitchDescription, ...] = (
    # Dynamic load balancing against the external meter; not used in PV Linkage.
    ThorConfigSwitchDescription(
        key="load_balancing",
        entity_category=EntityCategory.CONFIG,
        config_key="G_ExternalLimitPowerEnable",
        on_value=1,
        off_value=0,
        available_fn=lambda c: (
            c.supports("isSupportLoadBalancing")
            and c.charge_mode.get("mode") != MODE_PV_LINKAGE
        ),
    ),
    # Installer setting, disabled by default: unlock the cable at the charger once
    # it is unplugged from the EV.
    ThorConfigSwitchDescription(
        key="auto_unlock",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        config_key="UnlockConnectorOnEVSideDisconnect",
        on_value="true",
        off_value="false",
    ),
    # Installer setting, disabled by default, on models with a display only.
    # G_LCDCloseEnable turns on automatic screen-off, so "Disable" = display on.
    ThorConfigSwitchDescription(
        key="lcd_display",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        config_key="G_LCDCloseEnable",
        on_value="Disable",
        off_value="Enable",
        supported_fn=lambda c: c.supports("isSupport_LCDEnable"),
    ),
    # Warm-up: once the EV is full, keep supplying power so it can preheat in
    # cold weather instead of drawing on its battery.
    ThorConfigSwitchDescription(
        key="warm_up",
        entity_category=EntityCategory.CONFIG,
        config_key="G_FullContinueChargeEnable",
        on_value="Enable",
        off_value="Disable",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: charging, Boost and one switch per boolean setting it supports."""
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    entities: list[SwitchEntity] = []
    for sn, charger in coordinator.data.items():
        entities.append(ThorChargingSwitch(coordinator, sn))
        entities.append(ThorBoostSwitch(coordinator, sn))
        entities.append(ThorImportGridSwitch(coordinator, sn))
        for description in CONFIG_SWITCHES:
            if description.supported_fn is None or description.supported_fn(charger):
                entities.append(ThorConfigSwitch(coordinator, sn, description))
            elif entity_id := registry.async_get_entity_id(
                "switch", DOMAIN, f"{sn}_{description.key}"
            ):
                # Created for every model by older versions: drop it where unsupported.
                registry.async_remove(entity_id)
    async_add_entities(entities)


class ThorChargingSwitch(ThorEntity, SwitchEntity):
    """On while an OCPP transaction is running; toggling sends remote start/stop.

    In RFID mode sessions start and stop with a card only: toggling is refused.
    """

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "charging")

    @property
    def is_on(self) -> bool:
        # Suspended states still hold an open transaction, so they count as on.
        return self.charger.connector.get("status") in ACTIVE_STATES

    async def async_turn_on(self, **kwargs: Any) -> None:
        with ha_errors("Could not start charging"):
            check_remote_control(self.charger)
        try:
            await self.coordinator.api.async_start_charging(self._sn, CONNECTOR_ID)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not start charging: {err}") from err
        # State follows the charger, not the command: refresh to pick up the result.
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        with ha_errors("Could not stop charging"):
            check_remote_control(self.charger)
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
        await self.coordinator.async_request_refresh()


class ThorConfigSwitch(ThorEntity, SwitchEntity):
    """Switch backed by a single charger setting."""

    entity_description: ThorConfigSwitchDescription

    def __init__(
        self, coordinator, sn: str, description: ThorConfigSwitchDescription
    ) -> None:
        super().__init__(coordinator, sn, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        available_fn = self.entity_description.available_fn
        return super().available and (available_fn is None or available_fn(self.charger))

    @property
    def is_on(self) -> bool | None:
        raw = self.charger.config.get(self.entity_description.config_key)
        if raw is None:
            return None
        # The API may return the same setting as int, string or boolean.
        return str(raw).lower() == str(self.entity_description.on_value).lower()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(self.entity_description.on_value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(self.entity_description.off_value)

    async def _async_set(self, value: Any) -> None:
        """Write the setting, show it right away, then confirm with a refresh."""
        check_owner(self.charger)
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


class ThorImportGridSwitch(ThorEntity, SwitchEntity):
    """PV Linkage: let the grid top up the surplus, at the staged import power.

    Off sends no grid import (surplus only); the power stays staged for the
    next time it is turned on.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "import_grid")

    @property
    def available(self) -> bool:
        return super().available and self.charger.charge_mode.get("mode") == MODE_PV_LINKAGE

    @property
    def is_on(self) -> bool:
        return is_import_grid_on(self.charger)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, enabled: bool) -> None:
        with ha_errors("Could not set grid import"):
            await async_set_import_grid(
                self.coordinator, self._sn, effective_plan(self.coordinator, self._sn), enabled
            )
        self.async_write_ha_state()
        await self.coordinator.async_refresh_after_write()
