"""Repairs: fix a charger clock that differs from Home Assistant's.

The problem
-----------
Off-peak slots, Boost windows and scheduled starts run on the charger's own clock: a time
zone such as "UTC+1" (sysTimeZone) plus a daylight saving period set by date
(G_DaylightSavingTime, "03-28&10-31"). While that clock gives another UTC offset than Home
Assistant's local time, those times run early or late, so the coordinator raises the
"time_zone_mismatch" issue (GrowattThorCoordinator._check_clocks).

The fix
-------
The issue is fixable. Its flow shows the charger's clock next to Home Assistant's and what
will be set, then, once confirmed, sets on the charger the time zone and daylight saving
period that match Home Assistant's time zone (GrowattThorCoordinator.async_align_clock).
That happens once: the daylight saving dates are renewed every year only while the
"General - Clock from Home Assistant" switch is on. The issue goes away with the next
update, which reads the clock as written.

The issue's data carries the config entry id and the charger's serial number.
"""

from __future__ import annotations

from typing import Any

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .api import GrowattThorError
from .clock import NO_DAYLIGHT_SAVING, ClockError, charger_offset, format_offset, time_zone
from .coordinator import GrowattThorCoordinator


class ClockFixFlow(RepairsFlow):
    """Confirm, then set Home Assistant's clock on the charger."""

    def __init__(self, entry_id: str, sn: str) -> None:
        self._entry_id = entry_id
        self._sn = sn

    def _coordinator(self) -> GrowattThorCoordinator | None:
        """The charger's coordinator, or None once the integration or the charger is gone."""
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is None or entry.state is not ConfigEntryState.LOADED:
            return None
        coordinator: GrowattThorCoordinator = entry.runtime_data
        return coordinator if self._sn in coordinator.data else None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Show what will change; on confirmation, write it."""
        if (coordinator := self._coordinator()) is None:
            return self.async_abort(reason="not_loaded")
        try:
            if user_input is not None:
                await coordinator.async_align_clock(self._sn)
                return self.async_create_entry(data={})
            zone, daylight = await coordinator.async_clock_target()
        except ClockError:
            return self.async_abort(reason="no_matching_zone")
        except GrowattThorError:
            return self.async_abort(reason="cannot_write")

        charger = coordinator.data[self._sn]
        now = dt_util.now()
        offset = charger_offset(charger.config, now.date())
        start, _, end = daylight.partition("&")
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": charger.summary.get("name") or self._sn,
                "zone": time_zone(charger.config) or "",
                "charger_offset": format_offset(offset) if offset is not None else "?",
                "ha_offset": format_offset(now.utcoffset()),
                "new_zone": zone,
                # "03-28 → 10-31"; "-" without daylight saving.
                "new_daylight": "-" if daylight == NO_DAYLIGHT_SAVING else f"{start} → {end}",
            },
        )


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """The flow behind the "Fix" button of a time_zone_mismatch issue."""
    data = data or {}
    return ClockFixFlow(str(data.get("entry_id")), str(data.get("sn")))
