"""Config flow and entity tests for the Growatt THOR integration."""

from __future__ import annotations

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_thor_cloud.api import GrowattThorAuthError, hash_password
from custom_components.growatt_thor_cloud.const import CONF_PASSWORD_HASH, DOMAIN
from custom_components.growatt_thor_cloud.sensor import _in_slot

from .common import (
    call as _call,
    enable as _enable,
    set_charge_mode,
    set_charging,
    set_config,
    set_connector,
    setup_integration,
    state as _state,
    track_charge_mode,
)
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
    set_charging(mock_api)
    await setup_integration(hass)

    def state(domain: str, key: str) -> str:
        return _state(hass, domain, key).state

    assert state("sensor", "status") == "charging"
    assert state("sensor", "power") == "3680.0"
    assert state("sensor", "session_energy") == "3.5"
    assert _state(hass, "sensor", "session_cost").attributes["unit_of_measurement"] == "EUR"
    assert _state(hass, "sensor", "tariff").attributes["unit_of_measurement"] == "EUR/kWh"
    assert state("sensor", "tariff") == "0.21"  # From priceConf, not the session rate.
    assert state("sensor", "session_progress") == "unknown"  # No limit, no Boost.
    assert state("binary_sensor", "online") == "on"
    assert state("binary_sensor", "cable_lock") == "off"  # locked
    assert state("switch", "charging") == "on"
    assert state("switch", "load_balancing") == "unavailable"  # Not used in PV Linkage.
    assert state("switch", "warm_up") == "off"
    assert state("button", "unlock") == "unavailable"  # Not while charging.
    assert state("number", "max_current") == "32.0"
    assert state("switch", "import_grid") == "off"  # importGrid 0: surplus only.
    assert state("number", "import_grid_power") == "unknown"  # Nothing staged yet.
    assert _state(hass, "number", "import_grid_power").attributes["max"] == 7.0
    assert state("select", "charge_mode") == "pv_linkage"
    assert _state(hass, "select", "charge_mode").attributes["options"] == [
        "fast",
        "pv_linkage",
        "off_peak",
    ]
    assert state("select", "authorization_mode") == "plug_and_charge"
    assert state("sensor", "last_session") == "unknown"  # No session in the history.
    # Low-level and installer settings and the IP are registered but disabled by default.
    for domain, key in (
        ("sensor", "ip_address"),
        ("select", "solar_mode"),
        ("number", "solar_limit_power"),
        ("switch", "lcd_display"),
        ("switch", "auto_unlock"),
    ):
        assert _state(hass, domain, key) is None


async def test_diagnostics(hass: HomeAssistant, mock_api) -> None:
    """Network, clock and protection settings are exposed as diagnostics."""
    await setup_integration(hass)
    assert _state(hass, "sensor", "network_mode").state == "static"
    assert _state(hass, "sensor", "network_connection").state == "unknown"  # Not reported.
    assert _state(hass, "sensor", "protection_temperature").state == "80.0"
    assert _state(hass, "sensor", "meter_type").attributes["address"] == 1
    time_zone = _state(hass, "sensor", "time_zone")
    assert time_zone.state == "UTC+2"
    assert time_zone.attributes["daylight_saving_start"] is None


async def test_daylight_saving_dates(hass: HomeAssistant, mock_api) -> None:
    """The daylight saving period shows as month-day pairs."""
    set_config(mock_api, sysTimeZone="UTC+1", G_DaylightSavingTime="03-29&10-25", G_NetType="wifi")
    await setup_integration(hass)
    time_zone = _state(hass, "sensor", "time_zone")
    assert time_zone.state == "UTC+1"
    assert time_zone.attributes["daylight_saving_start"] == "03-29"
    assert time_zone.attributes["daylight_saving_end"] == "10-25"
    assert _state(hass, "sensor", "network_connection").state == "wifi"


async def test_controls(hass: HomeAssistant, mock_api) -> None:
    """Every control sends the right command in the right wire format."""
    set_charging(mock_api)
    set_charge_mode(mock_api, mode="fast")
    entry = await setup_integration(hass)
    await _enable(hass, entry, ("switch", "lcd_display"), ("switch", "auto_unlock"))
    assert _state(hass, "switch", "lcd_display").state == "on"
    assert _state(hass, "switch", "auto_unlock").state == "on"

    await _call(hass, "switch", "turn_off", "charging")
    mock_api.async_stop_charging.assert_awaited_once_with(SN, 1, "1234")

    await _call(hass, "switch", "turn_on", "charging")
    mock_api.async_start_charging.assert_awaited_once_with(SN, 1)

    # General settings can change during a session.
    await _call(hass, "number", "set_value", "max_current", value=16)
    mock_api.async_set_config.assert_awaited_with(SN, "G_MaxCurrent", "16")

    await _call(hass, "switch", "turn_off", "lcd_display")
    mock_api.async_set_config.assert_awaited_with(SN, "G_LCDCloseEnable", "Enable")

    await _call(hass, "switch", "turn_on", "load_balancing")
    mock_api.async_set_config.assert_awaited_with(SN, "G_ExternalLimitPowerEnable", 1)

    await _call(hass, "switch", "turn_on", "warm_up")
    mock_api.async_set_config.assert_awaited_with(SN, "G_FullContinueChargeEnable", "Enable")

    await _call(hass, "switch", "turn_off", "auto_unlock")
    mock_api.async_set_config.assert_awaited_with(
        SN, "UnlockConnectorOnEVSideDisconnect", "false"
    )


async def test_unlock(hass: HomeAssistant, mock_api) -> None:
    """The connector can be unlocked while no charge is in progress."""
    set_connector(mock_api, status="Finishing", elockstate="locked")
    await setup_integration(hass)
    await _call(hass, "button", "press", "unlock")
    mock_api.async_unlock.assert_awaited_once_with(SN, 1)


async def test_session_progress(hass: HomeAssistant, mock_api) -> None:
    """Progress towards the session limit, capped at 100 %."""
    set_charging(mock_api, cKey="G_SetEnergy", cValue="10")
    entry = await setup_integration(hass)
    assert _state(hass, "sensor", "session_progress").state == "35.0"

    set_charging(mock_api, cKey="G_SetTime", cValue="30")  # 42 of 30 minutes.
    await entry.runtime_data.async_refresh()
    assert _state(hass, "sensor", "session_progress").state == "100.0"


async def test_session_progress_smart_boost(hass: HomeAssistant, mock_api) -> None:
    """With smart Boost on, progress is the session energy against the Boost energy."""
    set_charging(mock_api)
    set_charge_mode(mock_api, boost=1, boostType="smart", config="contime=07:30&energy=7")
    await setup_integration(hass)
    assert _state(hass, "sensor", "session_progress").state == "50.0"


async def test_session_progress_needs_a_session(hass: HomeAssistant, mock_api) -> None:
    """Outside a session there is nothing to measure."""
    set_connector(mock_api, cKey="G_SetEnergy", cValue="10")  # Idle.
    await setup_integration(hass)
    assert _state(hass, "sensor", "session_progress").state == "unknown"


async def test_hidden_settings(hass: HomeAssistant, mock_api) -> None:
    """Low-level ECO settings work once enabled; the ECO limit only in ECO."""
    entry = await setup_integration(hass)
    await _enable(hass, entry, ("select", "solar_mode"), ("number", "solar_limit_power"))
    assert _state(hass, "select", "solar_mode").state == "eco_plus"
    assert _state(hass, "number", "solar_limit_power").state == "unavailable"  # Unused in ECO+.

    set_config(mock_api, G_SolarMode=1)  # The charger confirms ECO.
    await _call(hass, "select", "select_option", "solar_mode", option="eco")
    mock_api.async_set_config.assert_awaited_with(SN, "G_SolarMode", 1)
    await hass.async_block_till_done()
    assert _state(hass, "number", "solar_limit_power").state == "1.38"


async def test_charge_mode_fast(hass: HomeAssistant, mock_api) -> None:
    """Fast needs no other field."""
    await setup_integration(hass)
    await _call(hass, "select", "select_option", "charge_mode", option="fast")
    mock_api.async_set_charge_mode.assert_awaited_once_with(SN, 1, {"mode": "fast"})


async def test_import_grid(hass: HomeAssistant, mock_api) -> None:
    """Grid import sends the staged power with the PV Linkage object; off sends 0."""
    track_charge_mode(mock_api)
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError, match="power first"):
        await _call(hass, "switch", "turn_on", "import_grid")

    # Off: the power is only staged.
    await _call(hass, "number", "set_value", "import_grid_power", value=1.4)
    mock_api.async_set_charge_mode.assert_not_awaited()

    await _call(hass, "switch", "turn_on", "import_grid")
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
    assert _state(hass, "switch", "import_grid").state == "on"


async def test_import_grid_running(hass: HomeAssistant, mock_api) -> None:
    """While on, the power shows the charger's value and edits are sent at once."""
    track_charge_mode(mock_api, importGrid=1.5)
    await setup_integration(hass)
    assert _state(hass, "switch", "import_grid").state == "on"
    assert _state(hass, "number", "import_grid_power").state == "1.5"

    await _call(hass, "number", "set_value", "import_grid_power", value=2)
    assert mock_api.async_set_charge_mode.await_args.args[2]["importGrid"] == "2"

    await _call(hass, "switch", "turn_off", "import_grid")
    assert mock_api.async_set_charge_mode.await_args.args[2]["importGrid"] == "0"
    # The power stays staged for the next time.
    assert _state(hass, "number", "import_grid_power").state == "2.0"


async def test_import_grid_power_unavailable_outside_pv_linkage(
    hass: HomeAssistant, mock_api
) -> None:
    """The grid import only applies to PV Linkage."""
    mock_api.async_get_charge_mode.side_effect = lambda sn, cid: {**CHARGE_MODE, "mode": "fast"}
    await setup_integration(hass)
    assert _state(hass, "number", "import_grid_power").state == "unavailable"
    assert _state(hass, "switch", "import_grid").state == "unavailable"


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


# Anonymised from a real charge history entry.
SESSION = {
    "chargeId": SN,
    "connectorId": 1,
    "starttime": "2026-07-18 12:45:40",
    "endtime": "2026-07-18 12:59:15",
    "sysStartTime": 1784349940000,
    "sysEndTime": 1784350755000,
    "ctime": 13,
    "energy": 0.733,
    "cost": 0.11,
    "chargemode": "3",
}


async def test_last_session(hass: HomeAssistant, mock_api) -> None:
    """The last ended session stays visible after the live session values reset."""
    mock_api.async_get_sessions.side_effect = lambda sn, count: [dict(SESSION)]
    await setup_integration(hass)
    # Times are on the charger's clock (UTC+2 in the fixture).
    assert _state(hass, "sensor", "last_session").state == "2026-07-18T10:59:15+00:00"
    assert _state(hass, "sensor", "last_session_start").state == "2026-07-18T10:45:40+00:00"
    assert _state(hass, "sensor", "last_session_duration").state == "13.0"
    assert _state(hass, "sensor", "last_session_energy").state == "0.733"
    cost = _state(hass, "sensor", "last_session_cost")
    assert (cost.state, cost.attributes["unit_of_measurement"]) == ("0.11", "EUR")


async def test_last_session_read_when_charging_ends(hass: HomeAssistant, mock_api) -> None:
    """The history is read with the settings, and again as soon as a session ends."""
    set_charging(mock_api)
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    assert mock_api.async_get_sessions.await_count == 1

    await coordinator.async_refresh()  # Still charging: not read again.
    assert mock_api.async_get_sessions.await_count == 1

    mock_api.async_get_sessions.side_effect = lambda sn, count: [dict(SESSION)]
    set_connector(mock_api, status="Finishing")
    await coordinator.async_refresh()
    assert mock_api.async_get_sessions.await_count == 2
    assert _state(hass, "sensor", "last_session").state == "2026-07-18T10:59:15+00:00"


async def test_lcd_only_with_a_display(hass: HomeAssistant, mock_api) -> None:
    """Models without a display get no LCD switch; an older one is removed."""
    registry = er.async_get(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user",
        data={CONF_USERNAME: "user", CONF_PASSWORD_HASH: "hash"},
    )
    entry.add_to_hass(hass)
    old = registry.async_get_or_create(
        "switch", DOMAIN, f"{SN}_lcd_display", config_entry=entry
    )
    set_config(mock_api, isSupport_LCDEnable=False)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(old.entity_id) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("PVlink+", "pv_linkage_surplus"),
        ("PVlink", "pv_linkage_grid"),
        ("PVlink ManualBoost", "pv_linkage_grid"),
        ("Off Peak", "off_peak"),
        ("Fast", "fast"),
        ("FutureMode", "unknown"),
    ],
)
async def test_working_mode(hass: HomeAssistant, mock_api, raw: str, expected: str) -> None:
    """The mode the charger runs, with any Boost suffix left out."""
    set_config(mock_api, G_WorkingMode=raw)
    await setup_integration(hass)
    assert _state(hass, "sensor", "working_mode").state == expected
