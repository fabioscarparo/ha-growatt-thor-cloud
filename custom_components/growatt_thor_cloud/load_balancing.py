"""Load balancing: the household power limit, set by time slot.

What it is
----------
Load balancing keeps the household's total draw from the grid, home and charger
together, under a limit: the charger lowers its own power when the home needs more.
It needs the charger's grid meter or CT, and it is not used in PV Linkage.

How Growatt stores it
---------------------
The limit is a schedule of up to 10 time slots, read with the `selectLimitPower`
command and replaced as a whole with `updateLimitPower` (see API_NOTES.md):

    {"isEnable": 1, "cid": 4425, "config": [
        {"name": "Orario1", "time": "22:00-23:00", "loop": "1111100", "power": "5"}]}

- `time`: "HH:MM-HH:MM" on the charger's clock, both ends included. A slot may run
  past midnight ("22:00-06:00"). A limit for the whole day is one slot "00:00-23:59"
  on every day.
- `loop`: one flag per weekday, Monday first ("1111100" = Monday to Friday).
- `power`: the limit in kW, as text ("5", "4.5").
- `name`: only a label; any text is accepted.
- `cid`: the schedule's id, sent back when it is replaced.
- `isEnable`: the schedule is on (1) or off (0).

Rules for a schedule: 1 to 10 slots; slots must not overlap, whatever their days,
both ends included; a slot's start must differ from its end; every slot needs at least
one day. A schedule is always written with load balancing on.

The charger reports the limit it applies in the `G_ExternalLimitPower` setting.

How the integration exposes it
------------------------------
- sensor "Load balancing limit": `G_ExternalLimitPower`, with the slots as attributes;
- number "General - Load balancing all-day limit": one limit for the whole day, written
  as a single all-day slot;
- action `growatt_thor_cloud.set_load_balancing`: any schedule, from automations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time
import re
from typing import Any

from .charge_mode import MODE_PV_LINKAGE, format_kw
from .coordinator import GrowattThorCoordinator, ThorCharger
from .entity import check_owner, to_float

# Weekdays in the order of the `loop` flags, named as in Home Assistant's time conditions.
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
# A slot covering the whole day, every day: the schedule of a single all-day limit.
ALL_DAY = (time(0, 0), time(23, 59))
MAX_SLOTS = 10
# Bounds of a limit, kW. Growatt accepts any positive value; Home Assistant's number
# entity needs bounds, and these leave room for any home connection.
MIN_POWER = 1.0
MAX_POWER = 100.0
# Label of the slots when the schedule has none to follow (they are numbered: "Slot1").
DEFAULT_LABEL = "Slot"


class LoadBalancingError(ValueError):
    """A schedule that the charger would not accept, reported as a validation error."""


def in_use(charger: ThorCharger) -> bool:
    """Supported by the charger and in use: load balancing does not apply in PV Linkage."""
    return (
        charger.supports("isSupportLoadBalancing")
        and charger.charge_mode.get("mode") != MODE_PV_LINKAGE
    )


def turned_on(charger: ThorCharger) -> bool:
    """In use and turned on (the General - Load balancing switch)."""
    return in_use(charger) and str(charger.config.get("G_ExternalLimitPowerEnable")) == "1"


@dataclass(frozen=True)
class Slot:
    """One time slot of the schedule, with its limit."""

    start: time
    end: time  # Included: "22:00-23:00" runs until 23:00 included.
    power: float  # kW
    days: tuple[str, ...] = DAYS

    def to_api(self, name: str) -> dict[str, str]:
        """The slot as `updateLimitPower` takes it."""
        return {
            "loop": "".join("1" if day in self.days else "0" for day in DAYS),
            "name": name,
            "power": format_kw(self.power),
            "time": f"{self.start:%H:%M}-{self.end:%H:%M}",
        }

    def as_attribute(self) -> dict[str, Any]:
        """The slot as shown in the sensor's attributes."""
        return {
            "days": list(self.days),
            "from": f"{self.start:%H:%M}",
            "to": f"{self.end:%H:%M}",
            "power": self.power,
        }

    def minutes(self) -> set[int]:
        """The minutes of the day the slot covers, ends included, across midnight if needed."""
        start = self.start.hour * 60 + self.start.minute
        end = self.end.hour * 60 + self.end.minute
        if start <= end:
            return set(range(start, end + 1))
        return set(range(start, 24 * 60)) | set(range(end + 1))


def read_slots(schedule: dict[str, Any]) -> list[Slot]:
    """The slots of a schedule as Growatt returns it; malformed entries are skipped."""
    slots: list[Slot] = []
    for entry in schedule.get("config") or []:
        try:
            start_text, end_text = str(entry["time"]).split("-")
            start = time.fromisoformat(start_text)
            end = time.fromisoformat(end_text)
        except (KeyError, TypeError, ValueError):
            continue
        power = to_float(entry.get("power"))
        if power is None:
            continue
        loop = str(entry.get("loop") or "")
        days = tuple(day for day, flag in zip(DAYS, loop, strict=False) if flag == "1")
        slots.append(Slot(start, end, power, days))
    return slots


def schedule_attributes(charger: ThorCharger) -> dict[str, Any] | None:
    """Whether the schedule is on and its slots, for the limit sensor; None if not read."""
    schedule = charger.load_balancing
    if not schedule:
        return None
    return {
        "schedule_enabled": str(schedule.get("isEnable")) == "1",
        "slots": [slot.as_attribute() for slot in read_slots(schedule)],
    }


def all_day_limit(charger: ThorCharger) -> float | None:
    """The limit when the schedule is a single all-day slot; None for any other schedule."""
    slots = read_slots(charger.load_balancing)
    if len(slots) == 1 and (slots[0].start, slots[0].end) == ALL_DAY and slots[0].days == DAYS:
        return slots[0].power
    return None


def validate(slots: Sequence[Slot]) -> None:
    """Raise LoadBalancingError unless the charger would accept the schedule."""
    if not 1 <= len(slots) <= MAX_SLOTS:
        raise LoadBalancingError(f"A load balancing schedule has 1 to {MAX_SLOTS} slots")
    for number, slot in enumerate(slots, 1):
        if slot.start == slot.end:
            raise LoadBalancingError(f"Slot {number} starts and ends at {slot.start:%H:%M}")
        if not slot.days:
            raise LoadBalancingError(f"Slot {number} has no days")
        if not MIN_POWER <= slot.power <= MAX_POWER:
            raise LoadBalancingError(
                f"Slot {number}: the limit must be {MIN_POWER:g} to {MAX_POWER:g} kW"
            )
    # Overlaps count whatever the days: the charger compares the times only.
    covered = [slot.minutes() for slot in slots]
    for first in range(len(slots)):
        for second in range(first + 1, len(slots)):
            if covered[first] & covered[second]:
                raise LoadBalancingError(
                    f"Slots {first + 1} and {second + 1} overlap: slots must not overlap, "
                    "whatever their days"
                )


def _label(schedule: dict[str, Any]) -> str:
    """The label the current slots are numbered with ("Orario" for "Orario1")."""
    for entry in schedule.get("config") or []:
        label = re.sub(r"\d+$", "", str(entry.get("name") or ""))
        if label:
            return label
    return DEFAULT_LABEL


async def async_set_slots(
    coordinator: GrowattThorCoordinator, sn: str, slots: Sequence[Slot]
) -> None:
    """Replace a charger's schedule with `slots`, turning load balancing on.

    Raises LoadBalancingError for a schedule the charger would not accept, and
    GrowattThorError when the cloud refuses the write. The new schedule shows right away;
    the caller then refreshes, which reads it back once the charger has applied it.
    """
    charger = coordinator.data[sn]
    check_owner(charger)
    if not charger.supports("isSupportLoadBalancing"):
        raise LoadBalancingError("This charger does not support load balancing")
    validate(slots)
    schedule = charger.load_balancing
    label = _label(schedule)
    config = [slot.to_api(f"{label}{number}") for number, slot in enumerate(slots, 1)]
    await coordinator.api.async_set_load_balancing(sn, True, schedule.get("cid"), config)
    charger.load_balancing = {**schedule, "isEnable": 1, "config": config}
