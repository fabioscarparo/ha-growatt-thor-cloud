"""The tariff: the energy price by time slot, which Growatt uses for the cost of a session.

What it is
----------
Growatt works out the cost of every session (the "Session - Cost" and "Last charge -
Cost" sensors) from a tariff stored with the charger: a price per kWh for each time
slot of the day, in the charger's currency. The "Tariff" sensor shows the price in
effect now, and Off-peak starts from the cheapest slots when it has none of its own.

How Growatt stores it
---------------------
`priceConf`, in the charger list (`/ocpp/api/list`) and in its settings (`configInfo`):

    [{"time": "00:00-07:59", "price": "0.18"}, {"time": "08:00-23:59", "price": "0.25"}]

It is replaced as a whole with the `addPrice` command (see API_NOTES.md), which takes the
same entries plus a `name` that is only a label (Growatt's own tariff editor sends "").

- `time`: "HH:MM-HH:MM", both ends included, possibly past midnight (see time_slots.py).
- `price`: a number as text, per kWh.

Rules for a tariff, as Growatt's own tariff editor enforces them: 1 to 6 slots; a
slot's start must differ from its end; slots must not overlap. The slots need not cover
the whole day: a time outside every slot has no price.

How the integration exposes it
------------------------------
- sensor "Tariff": the price in effect now, with the slots as attributes;
- number "General - All-day tariff": one price for the whole day, written as a single
  "00:00-23:59" slot;
- action `growatt_thor_cloud.set_tariff`: any tariff, from automations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time
from typing import Any

from . import time_slots
from .coordinator import GrowattThorCoordinator, ThorCharger
from .entity import check_owner, to_float

MAX_SLOTS = 6
# Highest price per kWh. Growatt sets no bound; Home Assistant's number entity needs one,
# and this one leaves room for currencies with large units.
MAX_PRICE = 9999.0
# Prices are sent with up to this many decimals.
PRICE_DECIMALS = 4


class TariffError(ValueError):
    """A tariff that Growatt would not accept, reported as a validation error."""


@dataclass(frozen=True)
class TariffSlot:
    """One time slot of the tariff, with its price."""

    start: time
    end: time  # Included: "08:00-12:00" runs until 12:00 included.
    price: float  # Per kWh, in the charger's currency.

    def to_api(self) -> dict[str, str]:
        """The slot as `addPrice` takes it."""
        return {
            "time": time_slots.label(self.start, self.end),
            "price": price_text(self.price),
            "name": "",
        }

    def as_attribute(self) -> dict[str, Any]:
        """The slot as shown in the "Tariff" sensor's attributes."""
        return {"from": f"{self.start:%H:%M}", "to": f"{self.end:%H:%M}", "price": self.price}


def price_text(price: float) -> str:
    """A price as Growatt stores it: plain decimal text without trailing zeros ("0.21")."""
    text = f"{price:.{PRICE_DECIMALS}f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def read_slots(charger: ThorCharger) -> list[TariffSlot]:
    """The charger's tariff slots, in Growatt's order; malformed entries are skipped."""
    slots: list[TariffSlot] = []
    for entry in charger.price_conf:
        times = time_slots.parse(entry.get("time"))
        price = to_float(entry.get("price"))
        if times is not None and price is not None:
            slots.append(TariffSlot(*times, price))
    return slots


def tariff_attributes(charger: ThorCharger) -> dict[str, Any]:
    """The slots, for the "Tariff" sensor."""
    return {"slots": [slot.as_attribute() for slot in read_slots(charger)]}


def all_day_price(charger: ThorCharger) -> float | None:
    """The price when the tariff is a single slot covering the whole day; None otherwise.

    The slot need not start at midnight: "07:00-06:59" covers the whole day as well.
    """
    slots = read_slots(charger)
    if len(slots) != 1:
        return None
    slot = slots[0]
    if len(time_slots.minutes(slot.start, slot.end)) != time_slots.MINUTES_PER_DAY:
        return None
    return slot.price


def validate(slots: Sequence[TariffSlot]) -> None:
    """Raise TariffError unless Growatt would accept the tariff."""
    if not 1 <= len(slots) <= MAX_SLOTS:
        raise TariffError(f"A tariff has 1 to {MAX_SLOTS} slots")
    for number, slot in enumerate(slots, 1):
        if slot.start == slot.end:
            raise TariffError(f"Slot {number} starts and ends at {slot.start:%H:%M}")
        if not 0 <= slot.price <= MAX_PRICE:
            raise TariffError(f"Slot {number}: the price must be 0 to {MAX_PRICE:g}")
    if overlap := time_slots.first_overlap([(slot.start, slot.end) for slot in slots]):
        raise TariffError(f"Slots {overlap[0]} and {overlap[1]} overlap")


async def async_set_tariff(
    coordinator: GrowattThorCoordinator, sn: str, slots: Sequence[TariffSlot]
) -> None:
    """Replace a charger's tariff with `slots`.

    Raises TariffError for a tariff Growatt would not accept, and GrowattThorError when
    the cloud refuses the write. The new tariff shows right away; the caller then
    refreshes, which reads it back from the charger's settings.
    """
    charger = coordinator.data[sn]
    check_owner(charger)
    validate(slots)
    price_conf = [slot.to_api() for slot in slots]
    await coordinator.api.async_set_tariff(sn, price_conf)
    # ThorCharger.price_conf reads the settings first.
    charger.config["priceConf"] = price_conf
