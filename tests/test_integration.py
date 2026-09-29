"""Config flow and entity tests for the Growatt THOR integration."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_thor_cloud.api import GrowattThorAuthError, hash_password
from custom_components.growatt_thor_cloud.const import CONF_PASSWORD_HASH, DOMAIN
from custom_components.growatt_thor_cloud.sensor import _in_slot

from .conftest import SN


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    """Add a config entry and set it up against the mocked API."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user",
        data={CONF_USERNAME: "user", CONF_PASSWORD_HASH: "hash"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_user_flow_stores_only_hash(hass: HomeAssistant, mock_api) -> None:
    """The entry keeps the Growatt hash, never the plain password."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "secret"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_USERNAME: "user",
        CONF_PASSWORD_HASH: hash_password("secret"),
    }


async def test_user_flow_errors(hass: HomeAssistant, mock_api) -> None:
    """Rejected login and accounts without chargers are reported on the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_api.login.side_effect = GrowattThorAuthError("bad")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "x"}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    mock_api.login.side_effect = None
    mock_api.async_get_chargers.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "x"}
    )
    assert result["errors"] == {"base": "no_chargers"}


async def test_entities(hass: HomeAssistant, mock_api) -> None:
    """API payloads map to the expected entity states and units."""
    await _setup(hass)
    states = {s.entity_id: s for s in hass.states.async_all()}
    prefix = SN.lower()  # Entity ids derive from the device name (the serial).

    def state(domain: str, name: str) -> str:
        return states[f"{domain}.{prefix}_{name}"].state

    assert state("sensor", "status") == "charging"
    assert state("sensor", "charge_mode") == "pv_linkage"
    assert state("sensor", "power") == "3680.0"
    assert state("sensor", "session_energy") == "3.5"
    assert states[f"sensor.{prefix}_session_cost"].attributes["unit_of_measurement"] == "EUR"
    assert states[f"sensor.{prefix}_tariff"].attributes["unit_of_measurement"] == "EUR/kWh"
    assert state("sensor", "tariff") == "0.21"  # From priceConf, not the session rate.
    assert state("binary_sensor", "online") == "on"
    assert state("binary_sensor", "cable_lock") == "off"  # locked
    assert state("switch", "charging") == "on"
    assert state("number", "max_current") == "32.0"
    assert state("number", "solar_limit_power") == "1.38"
    assert states[f"number.{prefix}_solar_limit_power"].attributes["max"] == 7.0
    assert state("switch", "load_balancing") == "off"
    assert state("switch", "lcd_display") == "on"
    assert state("select", "solar_mode") == "eco_plus"
    assert state("select", "authorization_mode") == "plug_and_charge"
    assert f"sensor.{prefix}_ip_address" not in states  # disabled by default


async def test_controls(hass: HomeAssistant, mock_api) -> None:
    """Every control sends the right command in the right wire format."""
    await _setup(hass)
    prefix = SN.lower()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": f"switch.{prefix}_charging"}, blocking=True
    )
    mock_api.async_stop_charging.assert_awaited_once_with(SN, 1, "1234")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": f"switch.{prefix}_charging"}, blocking=True
    )
    mock_api.async_start_charging.assert_awaited_once_with(SN, 1)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": f"number.{prefix}_max_current", "value": 16},
        blocking=True,
    )
    mock_api.async_set_config.assert_awaited_with(SN, "G_MaxCurrent", "16")

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": f"select.{prefix}_solar_mode", "option": "eco"},
        blocking=True,
    )
    mock_api.async_set_config.assert_awaited_with(SN, "G_SolarMode", 1)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": f"switch.{prefix}_lcd_display"}, blocking=True
    )
    mock_api.async_set_config.assert_awaited_with(SN, "G_LCDCloseEnable", "Enable")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": f"switch.{prefix}_load_balancing"}, blocking=True
    )
    mock_api.async_set_config.assert_awaited_with(SN, "G_ExternalLimitPowerEnable", 1)


async def test_auth_failure_starts_reauth(hass: HomeAssistant, mock_api) -> None:
    """An auth error while polling starts the reauth flow."""
    mock_api.async_get_chargers.side_effect = GrowattThorAuthError("expired")
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="user", data={CONF_USERNAME: "user", CONF_PASSWORD_HASH: "h"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]


def test_tariff_slots() -> None:
    """Slots include their end minute and may wrap past midnight."""
    assert _in_slot("00:00-23:59", "23:59")
    assert _in_slot("22:00-08:00", "23:30")
    assert _in_slot("22:00-08:00", "07:00")
    assert not _in_slot("22:00-08:00", "12:00")
    assert not _in_slot("", "12:00")
