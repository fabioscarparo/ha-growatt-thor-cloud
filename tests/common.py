"""Helpers shared by the entity tests."""

from __future__ import annotations

from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_thor_cloud.const import CONF_PASSWORD_HASH, DOMAIN

from .conftest import CHARGE_MODE, CHARGING, CONFIG, CONNECTOR, SN


def set_connector(mock_api, reservations=(), **data) -> None:
    """Make charge/info return these connector fields, and the reservation list these."""
    mock_api.async_get_connector.side_effect = lambda sn, cid: {**CONNECTOR, **data}
    mock_api.async_get_reservations.side_effect = lambda sn, cid: [dict(r) for r in reservations]


def set_charging(mock_api, **data) -> None:
    """A running session, with these connector fields on top."""
    set_connector(mock_api, **{**CHARGING, **data})


def set_charge_mode(mock_api, **fields) -> None:
    mock_api.async_get_charge_mode.side_effect = lambda sn, cid: {**CHARGE_MODE, **fields}


def set_config(mock_api, **fields) -> None:
    mock_api.async_get_config.side_effect = lambda sn: {**CONFIG, **fields}


async def setup_integration(hass: HomeAssistant, options: dict | None = None) -> MockConfigEntry:
    """Add a config entry and set it up against the mocked API."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user",
        data={CONF_USERNAME: "user", CONF_PASSWORD_HASH: "hash"},
        options=options or {},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id(hass: HomeAssistant, domain: str, key: str) -> str:
    """Entity id by unique id, so tests do not depend on translated names."""
    found = er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{SN}_{key}")
    assert found, f"{domain} {key} not registered"
    return found


def state(hass: HomeAssistant, domain: str, key: str) -> State | None:
    return hass.states.get(entity_id(hass, domain, key))


async def call(hass: HomeAssistant, domain: str, service: str, key: str, **data) -> None:
    """Call an entity service on one of the charger's entities."""
    await hass.services.async_call(
        domain, service, {"entity_id": entity_id(hass, domain, key), **data}, blocking=True
    )


async def enable(hass: HomeAssistant, entry: MockConfigEntry, *entities: tuple[str, str]) -> None:
    """Enable entities that are disabled by default, then reload to create them."""
    registry = er.async_get(hass)
    for domain, key in entities:
        registry.async_update_entity(entity_id(hass, domain, key), disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
