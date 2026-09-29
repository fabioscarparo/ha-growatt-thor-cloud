"""Config flow and entity tests for the Growatt THOR integration."""

from __future__ import annotations

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_thor_cloud.api import GrowattThorAuthError, hash_password
from custom_components.growatt_thor_cloud.const import CONF_PASSWORD_HASH, DOMAIN
from custom_components.growatt_thor_cloud.sensor import _in_slot

from .common import call as _call, enable as _enable, setup_integration, state as _state
from .conftest import CHARGE_MODE, CONFIG, SN


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
    await setup_integration(hass)

    def state(domain: str, key: str) -> str:
        return _state(hass, domain, key).state

    assert state("sensor", "status") == "charging"
    assert state("sensor", "power") == "3680.0"
    assert state("sensor", "session_energy") == "3.5"
    assert _state(hass, "sensor", "session_cost").attributes["unit_of_measurement"] == "EUR"
    assert _state(hass, "sensor", "tariff").attributes["unit_of_measurement"] == "EUR/kWh"
    assert state("sensor", "tariff") == "0.21"  # From priceConf, not the session rate.
    assert state("binary_sensor", "online") == "on"
    assert state("binary_sensor", "cable_lock") == "off"  # locked
    assert state("switch", "charging") == "on"
    assert state("switch", "load_balancing") == "off"
    assert state("switch", "lcd_display") == "on"
    assert state("number", "max_current") == "32.0"
    assert state("number", "import_grid_power") == "0.0"
    assert _state(hass, "number", "import_grid_power").attributes["max"] == 7.0
    assert state("select", "charge_mode") == "pv_linkage"
    assert state("select", "authorization_mode") == "plug_and_charge"
    # Low-level settings and the IP are registered but disabled by default.
    for domain, key in (
        ("sensor", "ip_address"),
        ("select", "solar_mode"),
        ("number", "solar_limit_power"),
    ):
        assert _state(hass, domain, key) is None


async def test_controls(hass: HomeAssistant, mock_api) -> None:
    """Every control sends the right command in the right wire format."""
    await setup_integration(hass)

    await _call(hass, "switch", "turn_off", "charging")
    mock_api.async_stop_charging.assert_awaited_once_with(SN, 1, "1234")

    await _call(hass, "switch", "turn_on", "charging")
    mock_api.async_start_charging.assert_awaited_once_with(SN, 1)

    await _call(hass, "number", "set_value", "max_current", value=16)
    mock_api.async_set_config.assert_awaited_with(SN, "G_MaxCurrent", "16")

    await _call(hass, "switch", "turn_off", "lcd_display")
    mock_api.async_set_config.assert_awaited_with(SN, "G_LCDCloseEnable", "Enable")

    await _call(hass, "switch", "turn_on", "load_balancing")
    mock_api.async_set_config.assert_awaited_with(SN, "G_ExternalLimitPowerEnable", 1)


async def test_hidden_settings(hass: HomeAssistant, mock_api) -> None:
    """Low-level ECO settings work once the user enables them."""
    entry = await setup_integration(hass)
    await _enable(hass, entry, ("select", "solar_mode"), ("number", "solar_limit_power"))
    assert _state(hass, "select", "solar_mode").state == "eco_plus"
    assert _state(hass, "number", "solar_limit_power").state == "1.38"

    await _call(hass, "select", "select_option", "solar_mode", option="eco")
    mock_api.async_set_config.assert_awaited_with(SN, "G_SolarMode", 1)


async def test_charge_mode_fast(hass: HomeAssistant, mock_api) -> None:
    """Fast needs no other field."""
    await setup_integration(hass)
    await _call(hass, "select", "select_option", "charge_mode", option="fast")
    mock_api.async_set_charge_mode.assert_awaited_once_with(SN, 1, {"mode": "fast"})


async def test_import_grid_power(hass: HomeAssistant, mock_api) -> None:
    """Grid import resends the PV Linkage object with the meter setup from the config."""
    await setup_integration(hass)
    await _call(hass, "number", "set_value", "import_grid_power", value=1.4)
    mock_api.async_set_charge_mode.assert_awaited_once_with(
        SN,
        1,
        {
            "mode": "pvLinkage",
            "boost": "0",
            "boostType": "manual",
            "config": "",
            "G_ExternalSamplingCurWring": "1",
            "G_PowerMeterType": "Eastron SDM230",
            "importGrid": "1.4",
        },
    )


async def test_import_grid_power_unavailable_outside_pv_linkage(
    hass: HomeAssistant, mock_api
) -> None:
    """The grid import only applies to PV Linkage."""
    mock_api.async_get_charge_mode.side_effect = lambda sn, cid: {**CHARGE_MODE, "mode": "fast"}
    await setup_integration(hass)
    assert _state(hass, "number", "import_grid_power").state == "unavailable"


async def test_charge_mode_off_peak(hass: HomeAssistant, mock_api) -> None:
    """Off-peak defaults to the cheapest tariff slots; boost is not carried across modes."""
    tariffs = [
        {"price": "0.21", "time": "08:00-19:00"},
        {"price": "0.15", "time": "19:00-23:59"},
        {"price": "0.15", "time": "00:00-08:00"},
    ]
    mock_api.async_get_config.side_effect = lambda sn: {**CONFIG, "priceConf": tariffs}
    await setup_integration(hass)
    await _call(hass, "select", "select_option", "charge_mode", option="off_peak")
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["mode"] == "offPeak"
    assert fields["G_PeriodTime"] == "time1=19:00-23:59&time2=00:00-08:00"
    assert fields["boost"] == "0"


async def test_charge_mode_off_peak_keeps_user_slots(hass: HomeAssistant, mock_api) -> None:
    """Slots already chosen by the user win over the tariff default."""
    mock_api.async_get_charge_mode.side_effect = lambda sn, cid: {
        **CHARGE_MODE,
        "G_PeriodTime": "time1=01:00-06:00",
    }
    await setup_integration(hass)
    await _call(hass, "select", "select_option", "charge_mode", option="off_peak")
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["G_PeriodTime"] == "time1=01:00-06:00"


async def test_charge_mode_off_peak_needs_slots(hass: HomeAssistant, mock_api) -> None:
    """Without slots on the charger, tariffs or staged slots, Off-peak is refused."""
    mock_api.async_get_config.side_effect = lambda sn: {**CONFIG, "priceConf": []}
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError):
        await _call(hass, "select", "select_option", "charge_mode", option="off_peak")
    mock_api.async_set_charge_mode.assert_not_awaited()


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
