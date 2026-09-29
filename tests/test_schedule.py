"""Scheduled starts, reservations, Boost and the matching actions."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import mock_restore_cache_with_extra_data

from custom_components.growatt_thor_cloud.const import DOMAIN
from custom_components.growatt_thor_cloud.coordinator import ChargePlan, ThorCharger
from custom_components.growatt_thor_cloud.schedule import (
    PlanError,
    boost_fields,
    next_reservation,
    next_start,
)

from .common import call, entity_id, setup_integration, state
from .conftest import CHARGE_MODE, CONFIG, CONNECTOR, SN

RESERVATION = {
    "reservationId": 7,
    "chargeId": SN,
    "connectorId": 1,
    "expiryDate": "2026-09-29T23:00:00.000Z",
    "loopType": 0,
    "loopValue": "23:00",
    "cKey": "G_SetEnergy",
    "cValue": 20,
}


def _connector(mock_api, reservations=(), **data) -> None:
    """Make charge/info return these connector fields and reservations."""
    mock_api.async_get_connector.side_effect = lambda sn, cid: {
        "data": {**CONNECTOR, **data},
        "reservations": [dict(r) for r in reservations],
    }


def _charge_mode(mock_api, **fields) -> None:
    mock_api.async_get_charge_mode.side_effect = lambda sn, cid: {**CHARGE_MODE, **fields}


def _device_id(hass: HomeAssistant) -> str:
    """Device id of the charger, via one of its entities."""
    return er.async_get(hass).async_get(entity_id(hass, "sensor", "status")).device_id


# --- Pure helpers -----------------------------------------------------------


def test_next_start() -> None:
    """Today if still ahead, otherwise tomorrow."""
    now = datetime(2026, 9, 29, 10, 0)
    assert next_start(time(23, 0), now) == datetime(2026, 9, 29, 23, 0)
    assert next_start(time(9, 0), now) == datetime(2026, 9, 30, 9, 0)


def test_boost_fields() -> None:
    """Manual Boost sends a time window, smart Boost a departure time and energy."""
    charger = ThorCharger(sn=SN, summary={}, config=dict(CONFIG), charge_mode=dict(CHARGE_MODE))
    plan = ChargePlan(boost_from=time(10, 0), boost_to=time(12, 30))
    fields = boost_fields(charger, plan, True)
    assert (fields["boost"], fields["boostType"], fields["config"]) == (
        "1",
        "manual",
        "time1=10:00-12:30",
    )

    plan = ChargePlan(boost_type="smart", boost_departure=time(7, 5), boost_energy=15)
    assert boost_fields(charger, plan, True)["config"] == "contime=07:05&energy=15"
    assert boost_fields(charger, plan, False)["boost"] == "0"

    # Off-peak only has smart Boost: a manual choice is sent as smart.
    charger.charge_mode["mode"] = "offPeak"
    charger.charge_mode["G_PeriodTime"] = "time1=01:00-06:00"
    plan = ChargePlan(boost_type="manual", boost_departure=time(7, 0), boost_energy=20)
    fields = boost_fields(charger, plan, True)
    assert (fields["boostType"], fields["config"]) == ("smart", "contime=07:00&energy=20")
    assert fields["G_PeriodTime"] == "time1=01:00-06:00"
    charger.charge_mode["mode"] = "fast"
    with pytest.raises(PlanError):
        boost_fields(charger, plan, True)


def test_next_reservation_every_day(hass: HomeAssistant) -> None:
    """Every-day reservations resolve to the next occurrence of their time."""
    charger = ThorCharger(sn=SN, summary={}, reservations=[RESERVATION])
    start, raw = next_reservation(charger)
    assert (start.hour, start.minute) == (23, 0)
    assert start > dt_util.now()
    assert raw["reservationId"] == 7


# --- Entities ---------------------------------------------------------------


async def test_defaults(hass: HomeAssistant, mock_api) -> None:
    """Staged values start from sensible defaults; read-only meter info is exposed."""
    await setup_integration(hass)
    assert state(hass, "select", "charge_limit").state == "none"
    assert state(hass, "select", "start_mode").state == "now"
    assert state(hass, "select", "boost_type").state == "manual"
    # Nothing invented: values the charger does not keep stay unset.
    assert state(hass, "number", "limit_energy").state == "unknown"
    assert state(hass, "number", "limit_cost").attributes["unit_of_measurement"] == "EUR"
    assert state(hass, "time", "start_time").state == "unknown"
    assert state(hass, "time", "boost_from").state == "unknown"
    assert state(hass, "switch", "boost").state == "off"
    assert state(hass, "button", "cancel_reservation").state == "unavailable"
    assert state(hass, "sensor", "session_limit").state == "none"
    assert state(hass, "sensor", "next_reservation").state == "unknown"
    assert state(hass, "sensor", "sampling_device").state == "meter"
    assert state(hass, "sensor", "meter_type").state == "Eastron SDM230"


async def test_restore_staged_values(hass: HomeAssistant, mock_api) -> None:
    """Staged choices and values set by the user survive a restart."""
    prefix = SN.lower()
    mock_restore_cache_with_extra_data(
        hass,
        [
            (State(f"select.{prefix}_fast_charge_limit", "cost"), {}),
            (State(f"time.{prefix}_fast_start_time", "06:30:00"), {"plan_value": "06:30:00"}),
            (State(f"number.{prefix}_fast_cost_limit", "4.5"), {"plan_value": "4.5"}),
        ],
    )
    await setup_integration(hass)
    assert state(hass, "select", "charge_limit").state == "cost"
    assert state(hass, "time", "start_time").state == "06:30:00"
    assert state(hass, "number", "limit_cost").state == "4.5"


async def test_old_invented_values_are_dropped(hass: HomeAssistant, mock_api) -> None:
    """Values saved by older versions (made-up defaults) do not come back."""
    prefix = SN.lower()
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(f"number.{prefix}_fast_energy_limit", "10.0"),
                {"native_value": 10.0, "native_min_value": 0.5, "native_max_value": 200,
                 "native_step": 0.5, "native_unit_of_measurement": "kWh"},
            ),
            (State(f"time.{prefix}_fast_start_time", "22:00:00"), {}),
        ],
    )
    await setup_integration(hass)
    assert state(hass, "number", "limit_energy").state == "unknown"
    assert state(hass, "time", "start_time").state == "unknown"


async def test_start_now_with_limit(hass: HomeAssistant, mock_api) -> None:
    """The start button sends the staged limit with a remote start."""
    _charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    await call(hass, "select", "select_option", "charge_limit", option="energy")
    await call(hass, "number", "set_value", "limit_energy", value=20)
    await call(hass, "button", "press", "start_plan")
    mock_api.async_start_charging.assert_awaited_once_with(SN, 1, "G_SetEnergy", "20")

    await call(hass, "select", "select_option", "charge_limit", option="duration")
    await call(hass, "number", "set_value", "limit_duration", value=90)
    await call(hass, "button", "press", "start_plan")
    mock_api.async_start_charging.assert_awaited_with(SN, 1, "G_SetTime", "90")


async def test_start_every_day(hass: HomeAssistant, mock_api, freezer) -> None:
    """A timed start becomes a reservation at the next occurrence of the time."""
    freezer.move_to("2026-09-29 10:00:00-07:00")  # Tests run in US/Pacific.
    _charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    await call(hass, "select", "select_option", "start_mode", option="every_day")
    await call(hass, "time", "set_value", "start_time", time="23:15:00")
    await call(hass, "button", "press", "start_plan")

    args = mock_api.async_reserve_charging.await_args
    assert args.args[:2] == (SN, 1)
    assert args.args[2].strftime("%Y-%m-%d %H:%M") == "2026-09-29 23:15"
    assert args.kwargs == {"every_day": True, "limit_key": None, "limit_value": None}


async def test_reservations(hass: HomeAssistant, mock_api) -> None:
    """Reservations show up in the sensor and can be cancelled."""
    _connector(mock_api, reservations=[RESERVATION])
    await setup_integration(hass)
    sensor = state(hass, "sensor", "next_reservation")
    assert sensor.state not in ("unknown", "unavailable")
    assert sensor.attributes == {
        **sensor.attributes,
        "every_day": True,
        "limit": "energy",
        "limit_value": 20.0,
    }

    await call(hass, "button", "press", "cancel_reservation")
    mock_api.async_cancel_reservation.assert_awaited_once_with(SN, RESERVATION)


async def test_session_limit(hass: HomeAssistant, mock_api) -> None:
    """The running session's limit comes from the connector's cKey/cValue."""
    _connector(mock_api, cKey="G_SetTime", cValue="90")
    await setup_integration(hass)
    sensor = state(hass, "sensor", "session_limit")
    assert sensor.state == "duration"
    assert sensor.attributes["value"] == 90.0


async def test_boost_on(hass: HomeAssistant, mock_api) -> None:
    """Boost off: edits are only staged. Turning it on sends the staged window."""
    await setup_integration(hass)
    await call(hass, "time", "set_value", "boost_from", time="10:00:00")
    await call(hass, "time", "set_value", "boost_to", time="14:00:00")
    mock_api.async_set_charge_mode.assert_not_awaited()

    await call(hass, "switch", "turn_on", "boost")
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert (fields["mode"], fields["boost"], fields["boostType"], fields["config"]) == (
        "pvLinkage",
        "1",
        "manual",
        "time1=10:00-14:00",
    )


async def test_boost_running(hass: HomeAssistant, mock_api) -> None:
    """While Boost runs, entities show the charger's settings and edits are resent."""
    _charge_mode(mock_api, boost=1, boostType="smart", config="contime=07:30&energy=15")
    await setup_integration(hass)
    assert state(hass, "switch", "boost").state == "on"
    assert state(hass, "select", "boost_type").state == "smart"
    assert state(hass, "time", "boost_departure").state == "07:30:00"
    assert state(hass, "number", "boost_energy").state == "15.0"

    await call(hass, "number", "set_value", "boost_energy", value=25)
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["config"] == "contime=07:30&energy=25"
    assert fields["boost"] == "1"


async def test_boost_unavailable_in_fast(hass: HomeAssistant, mock_api) -> None:
    """Boost only exists in PV Linkage and Off-peak."""
    _charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    assert state(hass, "switch", "boost").state == "unavailable"


# --- Actions ----------------------------------------------------------------


async def test_action_start_charging(hass: HomeAssistant, mock_api) -> None:
    """The action sends its own values and leaves the staged ones alone."""
    _charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    await hass.services.async_call(
        DOMAIN,
        "start_charging",
        {"device_id": _device_id(hass), "limit": "cost", "value": 4.5},
        blocking=True,
    )
    mock_api.async_start_charging.assert_awaited_once_with(SN, 1, "G_SetAmount", "4.5")
    assert state(hass, "select", "charge_limit").state == "none"


async def test_action_validation(hass: HomeAssistant, mock_api) -> None:
    """Missing values are rejected before anything is sent."""
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "start_charging",
            {"device_id": _device_id(hass), "limit": "energy"},
            blocking=True,
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "cancel_reservation", {"device_id": _device_id(hass)}, blocking=True
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "cancel_reservation", {"device_id": "not-a-device"}, blocking=True
        )
    mock_api.async_start_charging.assert_not_awaited()


async def test_action_set_boost(hass: HomeAssistant, mock_api) -> None:
    """The Boost action sends its values and the Boost entities follow them."""
    await setup_integration(hass)
    await hass.services.async_call(
        DOMAIN,
        "set_boost",
        {
            "device_id": _device_id(hass),
            "enabled": True,
            "type": "smart",
            "departure": "06:45",
            "energy": 12,
        },
        blocking=True,
    )
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["config"] == "contime=06:45&energy=12"
    assert state(hass, "select", "boost_type").state == "smart"


# --- Mode gating and Off-peak slots ----------------------------------------


async def test_scheduled_start_only_in_fast(hass: HomeAssistant, mock_api) -> None:
    """Outside Fast the start button is unavailable and the action is rejected."""
    await setup_integration(hass)  # Fixture mode: PV Linkage.
    assert state(hass, "button", "start_plan").state == "unavailable"
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "start_charging", {"device_id": _device_id(hass)}, blocking=True
        )
    mock_api.async_start_charging.assert_not_awaited()


async def test_off_peak_slots_default_to_tariff(hass: HomeAssistant, mock_api) -> None:
    """Before any off-peak use, slots follow the cheapest tariff; unused slots are 00:00-00:00."""
    await setup_integration(hass)
    assert state(hass, "time", "off_peak_1_from").state == "00:00:00"
    assert state(hass, "time", "off_peak_1_to").state == "23:59:00"
    assert state(hass, "time", "off_peak_2_from").state == "00:00:00"
    assert state(hass, "time", "off_peak_2_to").state == "00:00:00"


async def test_off_peak_staged_then_used(hass: HomeAssistant, mock_api) -> None:
    """Outside Off-peak, slot edits are only staged, then sent when switching to Off-peak."""
    await setup_integration(hass)
    await call(hass, "time", "set_value", "off_peak_1_from", time="23:00:00")
    await call(hass, "time", "set_value", "off_peak_1_to", time="07:00:00")
    await call(hass, "time", "set_value", "off_peak_2_from", time="13:00:00")
    await call(hass, "time", "set_value", "off_peak_2_to", time="15:00:00")
    mock_api.async_set_charge_mode.assert_not_awaited()

    await call(hass, "select", "select_option", "charge_mode", option="off_peak")
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["G_PeriodTime"] == "time1=23:00-07:00&time2=13:00-15:00"


async def test_off_peak_live_edit_keeps_extra_slots(hass: HomeAssistant, mock_api) -> None:
    """In Off-peak, slot edits are sent at once; slots beyond the third are kept."""
    _charge_mode(
        mock_api,
        mode="offPeak",
        G_PeriodTime="time1=01:00-06:00&time2=12:00-14:00&time3=16:00-17:00&time4=20:00-21:00",
    )
    await setup_integration(hass)
    assert state(hass, "time", "off_peak_2_from").state == "12:00:00"

    await call(hass, "time", "set_value", "off_peak_2_to", time="15:00:00")
    fields = mock_api.async_set_charge_mode.await_args.args[2]
    assert fields["mode"] == "offPeak"
    assert fields["G_PeriodTime"] == (
        "time1=01:00-06:00&time2=12:00-15:00&time3=16:00-17:00&time4=20:00-21:00"
    )


async def test_off_peak_needs_one_slot(hass: HomeAssistant, mock_api) -> None:
    """Clearing the only slot while in Off-peak is rejected before anything is sent."""
    _charge_mode(mock_api, mode="offPeak", G_PeriodTime="time1=01:00-06:00")
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError):
        await call(hass, "time", "set_value", "off_peak_1_to", time="01:00:00")
    mock_api.async_set_charge_mode.assert_not_awaited()


async def test_unset_values_are_errors(hass: HomeAssistant, mock_api) -> None:
    """Using a value that was never set is reported instead of sending a made-up one."""
    _charge_mode(mock_api, mode="fast")
    await setup_integration(hass)
    await call(hass, "select", "select_option", "charge_limit", option="energy")
    with pytest.raises(ServiceValidationError):
        await call(hass, "button", "press", "start_plan")

    await call(hass, "select", "select_option", "charge_limit", option="none")
    await call(hass, "select", "select_option", "start_mode", option="at_time")
    with pytest.raises(ServiceValidationError):
        await call(hass, "button", "press", "start_plan")
    mock_api.async_start_charging.assert_not_awaited()
    mock_api.async_reserve_charging.assert_not_awaited()


async def test_boost_needs_its_settings(hass: HomeAssistant, mock_api) -> None:
    """Boost cannot be turned on before its window (manual) is set."""
    await setup_integration(hass)
    with pytest.raises(ServiceValidationError):
        await call(hass, "switch", "turn_on", "boost")
    mock_api.async_set_charge_mode.assert_not_awaited()
