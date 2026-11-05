"""Load balancing: the household power limit, read and set by time slot.

The charger keeps the limit as a schedule of time slots (selectLimitPower; see
custom_components/growatt_thor_cloud/load_balancing.py). These tests check:

- what the integration reads: the "Load balancing limit" sensor (G_ExternalLimitPower,
  with the slots as attributes) and the "all-day limit" number;
- when those entities are available: load balancing supported and not in PV Linkage,
  and, for the sensor, turned on;
- what it writes, for the all-day limit and for the set_load_balancing action: the
  format selectLimitPower returns (day flags from Monday, "HH:MM-HH:MM", kW as text);
- the schedules it refuses before sending anything.

The fixture schedule (conftest.LOAD_BALANCING) is one 5 kW slot for the whole day,
the shape a single all-day limit takes.
"""

from __future__ import annotations

import copy

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.growatt_thor_cloud.const import DOMAIN

from .common import call, entity_id, set_charge_mode, set_config, setup_integration, state
from .conftest import CHARGERS, LOAD_BALANCING, SN

EVERY_DAY = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
# Two slots, as Growatt returns them: weekday evenings and weekend evenings.
TWO_SLOTS = {
    **LOAD_BALANCING,
    "config": [
        {"loop": "1111100", "name": "Orario1", "power": "5", "time": "22:00-23:00"},
        {"loop": "0000011", "name": "Orario2", "power": "3.5", "time": "19:00-20:00"},
    ],
}


def _device_id(hass: HomeAssistant) -> str:
    """The charger's device, which the action targets."""
    return er.async_get(hass).async_get(entity_id(hass, "sensor", "status")).device_id


async def _setup(
    hass: HomeAssistant, mock_api, *, enabled: int = 1, schedule: dict | None = None, **config
) -> None:
    """Set up in Fast mode with load balancing on (or off), the given schedule and settings."""
    set_charge_mode(mock_api, mode="fast")
    set_config(mock_api, G_ExternalLimitPowerEnable=enabled, **config)
    if schedule is not None:
        mock_api.async_get_load_balancing.side_effect = lambda sn: copy.deepcopy(schedule)
    await setup_integration(hass)


async def _set_schedule(hass: HomeAssistant, slots: list[dict]) -> None:
    await hass.services.async_call(
        DOMAIN,
        "set_load_balancing",
        {"device_id": _device_id(hass), "slots": slots},
        blocking=True,
    )


async def test_all_day_limit_read(hass: HomeAssistant, mock_api) -> None:
    """A single all-day slot: the sensor shows the charger's limit, the number the slot's."""
    await _setup(hass, mock_api)

    limit = state(hass, "sensor", "load_balancing_limit")
    assert limit.state == "5.0"
    assert limit.attributes["unit_of_measurement"] == "kW"
    assert limit.attributes["schedule_enabled"] is True
    assert limit.attributes["slots"] == [
        {"days": EVERY_DAY, "from": "00:00", "to": "23:59", "power": 5.0}
    ]
    assert state(hass, "number", "load_balancing_all_day").state == "5.0"
    assert state(hass, "switch", "load_balancing").state == "on"
    # Read with the settings, not on every poll.
    mock_api.async_get_load_balancing.assert_awaited_once_with(SN)


async def test_time_slots_read(hass: HomeAssistant, mock_api) -> None:
    """With time slots there is no single all-day limit; the slots list their days."""
    await _setup(hass, mock_api, schedule=TWO_SLOTS)

    assert state(hass, "number", "load_balancing_all_day").state == "unknown"
    assert state(hass, "sensor", "load_balancing_limit").attributes["slots"] == [
        {"days": ["mon", "tue", "wed", "thu", "fri"], "from": "22:00", "to": "23:00", "power": 5.0},
        {"days": ["sat", "sun"], "from": "19:00", "to": "20:00", "power": 3.5},
    ]


@pytest.mark.parametrize(
    ("mode", "enabled", "sensor", "number"),
    [
        ("fast", 1, "5.0", "5.0"),
        # Turned off: no limit in force, but the all-day limit can still be set.
        ("fast", 0, "unavailable", "5.0"),
        # Load balancing does not apply in PV Linkage.
        ("pvLinkage", 1, "unavailable", "unavailable"),
    ],
)
async def test_availability(
    hass: HomeAssistant, mock_api, mode: str, enabled: int, sensor: str, number: str
) -> None:
    """The sensor needs load balancing on; both need it in use, outside PV Linkage."""
    set_charge_mode(mock_api, mode=mode)
    set_config(mock_api, G_ExternalLimitPowerEnable=enabled)
    await setup_integration(hass)

    assert state(hass, "sensor", "load_balancing_limit").state == sensor
    assert state(hass, "number", "load_balancing_all_day").state == number


async def test_unsupported_charger(hass: HomeAssistant, mock_api) -> None:
    """Without load balancing the schedule is not read and cannot be written."""
    await _setup(hass, mock_api, isSupportLoadBalancing=False)

    mock_api.async_get_load_balancing.assert_not_awaited()
    assert state(hass, "sensor", "load_balancing_limit").state == "unavailable"
    assert state(hass, "number", "load_balancing_all_day").state == "unavailable"
    with pytest.raises(ServiceValidationError):
        await _set_schedule(hass, [{"from": "00:00", "to": "23:59", "power": 5}])
    mock_api.async_set_load_balancing.assert_not_awaited()


async def test_set_all_day_limit(hass: HomeAssistant, mock_api) -> None:
    """The all-day limit replaces any schedule with one all-day slot, labelled like the others."""
    await _setup(hass, mock_api, schedule=TWO_SLOTS)

    await call(hass, "number", "set_value", "load_balancing_all_day", value=4.5)

    mock_api.async_set_load_balancing.assert_awaited_once_with(
        SN,
        True,
        4425,
        [{"loop": "1111111", "name": "Orario1", "power": "4.5", "time": "00:00-23:59"}],
    )
    # Shown right away; the settings are read again once the charger has applied it.
    assert state(hass, "number", "load_balancing_all_day").state == "4.5"
    assert state(hass, "sensor", "load_balancing_limit").attributes["slots"] == [
        {"days": EVERY_DAY, "from": "00:00", "to": "23:59", "power": 4.5}
    ]


async def test_action_set_load_balancing(hass: HomeAssistant, mock_api) -> None:
    """The action writes the slots in order, days as flags from Monday, whole kW without ".0"."""
    await _setup(hass, mock_api)

    await _set_schedule(
        hass,
        [
            {"from": "00:00", "to": "06:59", "power": 6},
            # Days in any order; seconds are dropped.
            {"from": "07:00:30", "to": "23:59", "power": 3.5, "days": ["fri", "mon"]},
        ],
    )

    mock_api.async_set_load_balancing.assert_awaited_once_with(
        SN,
        True,
        4425,
        [
            {"loop": "1111111", "name": "Orario1", "power": "6", "time": "00:00-06:59"},
            {"loop": "1000100", "name": "Orario2", "power": "3.5", "time": "07:00-23:59"},
        ],
    )
    assert state(hass, "number", "load_balancing_all_day").state == "unknown"


async def test_action_needs_the_owner(hass: HomeAssistant, mock_api) -> None:
    """A charger shared with the account cannot have its settings changed."""
    mock_api.async_get_chargers.return_value = [{**copy.deepcopy(CHARGERS[0]), "type": 1}]
    await _setup(hass, mock_api)

    with pytest.raises(ServiceValidationError):
        await _set_schedule(hass, [{"from": "00:00", "to": "23:59", "power": 5}])
    mock_api.async_set_load_balancing.assert_not_awaited()


@pytest.mark.parametrize(
    "slots",
    [
        pytest.param([], id="no slots"),
        pytest.param(
            [{"from": f"{hour:02d}:00", "to": f"{hour:02d}:30", "power": 5} for hour in range(11)],
            id="more than 10 slots",
        ),
        pytest.param([{"from": "08:00", "to": "08:00", "power": 5}], id="start equals end"),
        pytest.param([{"from": "08:00", "to": "09:00", "power": 5, "days": []}], id="no days"),
        pytest.param(
            [
                {"from": "22:00", "to": "06:00", "power": 5},
                {"from": "05:00", "to": "07:00", "power": 4},
            ],
            id="overlap past midnight",
        ),
        pytest.param(
            [
                {"from": "08:00", "to": "12:00", "power": 5, "days": ["mon"]},
                {"from": "12:00", "to": "14:00", "power": 4, "days": ["sat"]},
            ],
            id="shared minute on other days",
        ),
    ],
)
async def test_action_rejects_invalid_schedules(
    hass: HomeAssistant, mock_api, slots: list[dict]
) -> None:
    """Schedules the charger would not accept are refused before anything is sent."""
    await _setup(hass, mock_api)

    with pytest.raises(ServiceValidationError):
        await _set_schedule(hass, slots)
    mock_api.async_set_load_balancing.assert_not_awaited()


async def test_action_rejects_out_of_range_power(hass: HomeAssistant, mock_api) -> None:
    """The limit must be 1 to 100 kW, checked by the action's schema."""
    await _setup(hass, mock_api)

    with pytest.raises(vol.Invalid):
        await _set_schedule(hass, [{"from": "00:00", "to": "23:59", "power": 0.5}])
    mock_api.async_set_load_balancing.assert_not_awaited()
