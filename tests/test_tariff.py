"""The tariff: the energy price by time slot, read and set from Home Assistant.

Growatt keeps the tariff with the charger as a list of time slots with a price per kWh
(priceConf; see custom_components/growatt_thor_cloud/tariff.py). These tests check:

- what the integration reads: the slots in the "Tariff" sensor's attributes, and the
  "General - All-day tariff" number, which shows a price only while the tariff is a
  single slot covering the whole day;
- what it writes, for the all-day tariff and for the set_tariff action: the entries
  `addPrice` takes ("HH:MM-HH:MM", the price as plain text, an empty name);
- the tariffs it refuses before sending anything, and that only the owner may set one.

The fixture tariff (conftest.CONFIG) is one slot for the whole day at 0.21 EUR/kWh.
"""

from __future__ import annotations

import copy

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.growatt_thor_cloud.const import DOMAIN

from .common import call, entity_id, set_config, setup_integration, state
from .conftest import CHARGERS, SN

# Two slots, as Growatt returns them: a cheaper night past midnight, then the day.
TWO_SLOTS = [
    {"price": "0.18", "time": "22:00-06:59"},
    {"price": "0.25", "time": "07:00-21:59"},
]


def _device_id(hass: HomeAssistant) -> str:
    """The charger's device, which the action targets."""
    return er.async_get(hass).async_get(entity_id(hass, "sensor", "status")).device_id


async def _set_tariff(hass: HomeAssistant, slots: list[dict]) -> None:
    await hass.services.async_call(
        DOMAIN, "set_tariff", {"device_id": _device_id(hass), "slots": slots}, blocking=True
    )


async def test_all_day_tariff_read(hass: HomeAssistant, mock_api) -> None:
    """One slot for the whole day: the number shows its price, the sensor lists the slot."""
    await setup_integration(hass)

    number = state(hass, "number", "tariff_all_day")
    assert number.state == "0.21"
    assert number.attributes["unit_of_measurement"] == "EUR/kWh"
    assert state(hass, "sensor", "tariff").attributes["slots"] == [
        {"from": "00:00", "to": "23:59", "price": 0.21}
    ]


async def test_time_slots_read(hass: HomeAssistant, mock_api) -> None:
    """With time slots there is no single all-day price; the sensor lists them in order."""
    set_config(mock_api, priceConf=TWO_SLOTS)
    await setup_integration(hass)

    assert state(hass, "number", "tariff_all_day").state == "unknown"
    assert state(hass, "sensor", "tariff").attributes["slots"] == [
        {"from": "22:00", "to": "06:59", "price": 0.18},
        {"from": "07:00", "to": "21:59", "price": 0.25},
    ]


async def test_whole_day_from_another_time(hass: HomeAssistant, mock_api) -> None:
    """A single slot covers the whole day also when it does not start at midnight."""
    set_config(mock_api, priceConf=[{"price": "0.3", "time": "07:00-06:59"}])
    await setup_integration(hass)

    assert state(hass, "number", "tariff_all_day").state == "0.3"


async def test_set_all_day_tariff(hass: HomeAssistant, mock_api) -> None:
    """The all-day tariff replaces any slots with one slot from 00:00 to 23:59."""
    set_config(mock_api, priceConf=TWO_SLOTS)
    await setup_integration(hass)

    await call(hass, "number", "set_value", "tariff_all_day", value=0.245)

    mock_api.async_set_tariff.assert_awaited_once_with(
        SN, [{"time": "00:00-23:59", "price": "0.245", "name": ""}]
    )
    # Shown right away; the settings are read again once the write is confirmed.
    assert state(hass, "number", "tariff_all_day").state == "0.245"
    assert state(hass, "sensor", "tariff").attributes["slots"] == [
        {"from": "00:00", "to": "23:59", "price": 0.245}
    ]


async def test_action_set_tariff(hass: HomeAssistant, mock_api) -> None:
    """The action writes the slots in order, prices as plain text without trailing zeros."""
    await setup_integration(hass)

    await _set_tariff(
        hass,
        [
            {"from": "22:00", "to": "06:59", "price": 0.18},
            # Seconds are dropped; whole prices have no decimals.
            {"from": "07:00:30", "to": "21:59", "price": 1},
        ],
    )

    mock_api.async_set_tariff.assert_awaited_once_with(
        SN,
        [
            {"time": "22:00-06:59", "price": "0.18", "name": ""},
            {"time": "07:00-21:59", "price": "1", "name": ""},
        ],
    )
    assert state(hass, "number", "tariff_all_day").state == "unknown"


async def test_action_needs_the_owner(hass: HomeAssistant, mock_api) -> None:
    """A charger shared with the account cannot have its tariff changed."""
    mock_api.async_get_chargers.return_value = [{**copy.deepcopy(CHARGERS[0]), "type": 1}]
    await setup_integration(hass)

    with pytest.raises(ServiceValidationError):
        await _set_tariff(hass, [{"from": "00:00", "to": "23:59", "price": 0.2}])
    mock_api.async_set_tariff.assert_not_awaited()


@pytest.mark.parametrize(
    "slots",
    [
        pytest.param([], id="no slots"),
        pytest.param(
            [
                {"from": f"{hour:02d}:00", "to": f"{hour:02d}:30", "price": 0.2}
                for hour in range(7)
            ],
            id="more than 6 slots",
        ),
        pytest.param([{"from": "08:00", "to": "08:00", "price": 0.2}], id="start equals end"),
        pytest.param(
            [
                {"from": "07:00", "to": "12:00", "price": 0.2},
                {"from": "12:00", "to": "14:00", "price": 0.3},
            ],
            id="shared end minute",
        ),
        pytest.param(
            [
                {"from": "22:00", "to": "06:00", "price": 0.2},
                {"from": "05:00", "to": "07:00", "price": 0.3},
            ],
            id="overlap past midnight",
        ),
    ],
)
async def test_action_rejects_invalid_tariffs(
    hass: HomeAssistant, mock_api, slots: list[dict]
) -> None:
    """Tariffs that Growatt would not accept are refused before anything is sent."""
    await setup_integration(hass)

    with pytest.raises(ServiceValidationError):
        await _set_tariff(hass, slots)
    mock_api.async_set_tariff.assert_not_awaited()


async def test_action_rejects_negative_price(hass: HomeAssistant, mock_api) -> None:
    """A price below 0 is refused by the action's schema."""
    await setup_integration(hass)

    with pytest.raises(vol.Invalid):
        await _set_tariff(hass, [{"from": "00:00", "to": "23:59", "price": -0.1}])
    mock_api.async_set_tariff.assert_not_awaited()
