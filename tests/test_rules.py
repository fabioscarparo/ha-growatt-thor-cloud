"""When things may change: open sessions, RFID mode, shared chargers, model features."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.growatt_thor_cloud.const import DOMAIN

from .common import (
    call,
    entity_id,
    set_charge_mode,
    set_charging,
    set_config,
    set_connector,
    setup_integration,
    state,
)
from .conftest import CONFIG


def _device_id(hass: HomeAssistant) -> str:
    return er.async_get(hass).async_get(entity_id(hass, "sensor", "status")).device_id


# --- Open session -------------------------------------------------------------


async def test_mode_locked_during_session(hass: HomeAssistant, mock_api) -> None:
    """While charging the mode and its settings are refused, but stay visible."""
    set_charging(mock_api)
    set_charge_mode(
        mock_api, boost=1, boostType="smart", config="contime=07:30&energy=15", importGrid=1.0
    )
    await setup_integration(hass)
    assert state(hass, "select", "charge_mode").state == "pv_linkage"
    assert state(hass, "switch", "boost").state == "on"
    assert state(hass, "switch", "import_grid").state == "on"

    for domain, service, key, data in (
        ("select", "select_option", "charge_mode", {"option": "fast"}),
        ("switch", "turn_off", "boost", {}),
        ("switch", "turn_off", "import_grid", {}),
        # Live while their switches are on.
        ("number", "set_value", "import_grid_power", {"value": 1.4}),
        ("number", "set_value", "boost_energy", {"value": 20}),
    ):
        with pytest.raises(ServiceValidationError, match="Stop charging"):
            await call(hass, domain, service, key, **data)
    mock_api.async_set_charge_mode.assert_not_awaited()
    assert state(hass, "number", "boost_energy").state == "15.0"


async def test_off_peak_slots_locked_while_finishing(hass: HomeAssistant, mock_api) -> None:
    """A closing session still holds the Off-peak slots."""
    set_connector(mock_api, status="Finishing")
    set_charge_mode(mock_api, mode="offPeak", G_PeriodTime="time1=01:00-06:00")
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError):
        await call(hass, "time", "set_value", "off_peak_1_to", time="07:00:00")
    assert state(hass, "time", "off_peak_1_to").state == "06:00:00"
    mock_api.async_set_charge_mode.assert_not_awaited()


async def test_staging_allowed_during_session(hass: HomeAssistant, mock_api) -> None:
    """Values that are only staged (Boost off) can still be prepared."""
    set_charging(mock_api)
    await setup_integration(hass)
    await call(hass, "time", "set_value", "boost_from", time="10:00:00")
    assert state(hass, "time", "boost_from").state == "10:00:00"
    mock_api.async_set_charge_mode.assert_not_awaited()


async def test_fast_start_waits_for_session_end(hass: HomeAssistant, mock_api) -> None:
    """Limits and scheduled starts wait for the open session to end."""
    set_charging(mock_api, status="SuspendedEV")
    set_charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    assert state(hass, "button", "start_plan").state == "unavailable"
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "start_charging", {"device_id": _device_id(hass)}, blocking=True
        )
    mock_api.async_start_charging.assert_not_awaited()


# --- RFID mode ------------------------------------------------------------------


async def test_rfid_mode_refuses_remote_start_stop(hass: HomeAssistant, mock_api) -> None:
    """With RFID authorization, sessions start and stop with a card only."""
    set_config(mock_api, G_ChargerMode="2")
    set_charging(mock_api)
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError, match="RFID"):
        await call(hass, "switch", "turn_off", "charging")
    with pytest.raises(ServiceValidationError, match="RFID"):
        await call(hass, "switch", "turn_on", "charging")
    mock_api.async_stop_charging.assert_not_awaited()
    mock_api.async_start_charging.assert_not_awaited()


async def test_rfid_mode_allows_scheduled_starts(hass: HomeAssistant, mock_api) -> None:
    """A start now is refused in RFID mode; a scheduled one is still sent."""
    set_config(mock_api, G_ChargerMode="2")
    set_charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError, match="RFID"):
        await call(hass, "button", "press", "start_plan")

    await call(hass, "select", "select_option", "start_mode", option="at_time")
    await call(hass, "time", "set_value", "start_time", time="23:00:00")
    await call(hass, "button", "press", "start_plan")
    mock_api.async_reserve_charging.assert_awaited_once()
    mock_api.async_start_charging.assert_not_awaited()


# --- Shared chargers --------------------------------------------------------------


async def test_shared_charger_is_read_only(hass: HomeAssistant, mock_api) -> None:
    """On a charger shared with the account, settings and modes are refused."""
    mock_api.async_get_chargers.return_value[0]["type"] = 1
    await setup_integration(hass)
    for domain, service, key, data in (
        ("number", "set_value", "max_current", {"value": 16}),
        ("switch", "turn_on", "warm_up", {}),
        ("select", "select_option", "authorization_mode", {"option": "rfid"}),
        ("select", "select_option", "charge_mode", {"option": "fast"}),
    ):
        with pytest.raises(ServiceValidationError, match="owner"):
            await call(hass, domain, service, key, **data)
    mock_api.async_set_config.assert_not_awaited()
    mock_api.async_set_charge_mode.assert_not_awaited()

    # Starting a session stays possible.
    await call(hass, "switch", "turn_on", "charging")
    mock_api.async_start_charging.assert_awaited_once()


# --- Model features ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("flags", "options"),
    [
        ({"isSupportPL": False}, ["fast", "off_peak"]),
        ({"isSupportLoadBalancing": False, "isSupportLowRateMode": False}, ["fast"]),
        ({"isSupportPL": "false", "isSupportLowRateMode": "true"}, ["fast", "off_peak"]),
    ],
)
async def test_modes_follow_features(
    hass: HomeAssistant, mock_api, flags: dict, options: list[str]
) -> None:
    """Only the modes the charger supports are offered."""
    set_config(mock_api, **flags)
    set_charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    assert state(hass, "select", "charge_mode").attributes["options"] == options


async def test_modes_without_feature_flags(hass: HomeAssistant, mock_api) -> None:
    """Without feature flags every mode is offered; the current one is always listed."""
    config = {k: v for k, v in CONFIG.items() if not k.startswith("isSupport")}
    mock_api.async_get_config.side_effect = lambda sn: dict(config)
    await setup_integration(hass)
    options = ["fast", "pv_linkage", "off_peak"]
    assert state(hass, "select", "charge_mode").attributes["options"] == options


async def test_current_mode_stays_listed(hass: HomeAssistant, mock_api) -> None:
    """A mode the charger runs is listed even if its flag says otherwise."""
    set_config(mock_api, isSupportPL=False)  # Fixture mode: PV Linkage.
    await setup_integration(hass)
    charge_mode = state(hass, "select", "charge_mode")
    assert charge_mode.state == "pv_linkage"
    assert charge_mode.attributes["options"] == ["fast", "pv_linkage", "off_peak"]


@pytest.mark.parametrize(
    ("mode", "flag", "expected"),
    [("fast", True, "off"), ("offPeak", True, "off"), ("pvLinkage", True, "unavailable"),
     ("fast", False, "unavailable")],
)
async def test_load_balancing_availability(
    hass: HomeAssistant, mock_api, mode: str, flag: bool, expected: str
) -> None:
    """Load balancing applies outside PV Linkage, on chargers that support it."""
    set_config(mock_api, isSupportLoadBalancing=flag)
    set_charge_mode(mock_api, mode=mode, G_PeriodTime="time1=01:00-06:00")
    await setup_integration(hass)
    assert state(hass, "switch", "load_balancing").state == expected


@pytest.mark.parametrize(
    ("power", "maximum"),
    [(7000, 32), (3600, 16), (11000, 16), (22000, 32), (None, 32)],
)
async def test_max_current_follows_rating(
    hass: HomeAssistant, mock_api, power: int | None, maximum: int
) -> None:
    """Three-phase 11 kW and single-phase 3.6 kW chargers stop at 16 A."""
    set_config(mock_api, power=power)
    await setup_integration(hass)
    assert state(hass, "number", "max_current").attributes["max"] == maximum


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("Available", "unknown"),
        ("Accepted", "unknown"),
        ("SuspendedEV", "unknown"),
        ("Charging", "unavailable"),
        ("Faulted", "unavailable"),
    ],
)
async def test_unlock_availability(
    hass: HomeAssistant, mock_api, status: str, expected: str
) -> None:
    """Unlocking is offered while no charge is in progress."""
    set_connector(mock_api, status=status)
    await setup_integration(hass)
    assert state(hass, "button", "unlock").state == expected
