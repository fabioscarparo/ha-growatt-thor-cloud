"""Time slots of the day, as Growatt writes them: "HH:MM-HH:MM", both ends included.

Load balancing (load_balancing.py) and the tariff (tariff.py) keep their schedules as
lists of such slots, and Growatt applies the same rules to both:

- a slot covers every minute from its start to its end, both included: "07:00-12:00"
  ends at 12:00 included, so it overlaps a slot that starts at 12:00;
- a slot whose start comes after its end runs past midnight: "22:00-06:00" covers
  22:00 to 23:59 and then 00:00 to 06:00;
- "00:00-23:59" covers the whole day;
- a slot's start must differ from its end.

The helpers below read a slot, list the minutes it covers and find overlaps; each
module adds its own rules (number of slots, values) on top.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import time

MINUTES_PER_DAY = 24 * 60
# The slot that covers the whole day.
WHOLE_DAY = (time(0, 0), time(23, 59))


def parse(text: object) -> tuple[time, time] | None:
    """(start, end) of an "HH:MM-HH:MM" slot; None when `text` is not one."""
    try:
        start, end = str(text).split("-")
        return time.fromisoformat(start), time.fromisoformat(end)
    except ValueError:
        return None


def label(start: time, end: time) -> str:
    """A slot as Growatt writes it: "HH:MM-HH:MM"."""
    return f"{start:%H:%M}-{end:%H:%M}"


def minutes(start: time, end: time) -> set[int]:
    """The minutes of the day a slot covers (0 = 00:00), ends included, across midnight."""
    first = start.hour * 60 + start.minute
    last = end.hour * 60 + end.minute
    if first <= last:
        return set(range(first, last + 1))
    return set(range(first, MINUTES_PER_DAY)) | set(range(last + 1))


def first_overlap(slots: Sequence[tuple[time, time]]) -> tuple[int, int] | None:
    """Positions (from 1) of the first two slots that share a minute; None if none do."""
    covered = [minutes(start, end) for start, end in slots]
    for first in range(len(covered)):
        for second in range(first + 1, len(covered)):
            if covered[first] & covered[second]:
                return first + 1, second + 1
    return None
