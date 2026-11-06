"""Text settings: the start and end of the charger's daylight saving period.

The charger keeps its daylight saving period as one setting, G_DaylightSavingTime =
"MM-DD&MM-DD" ("03-28&10-31": from March 28 to October 31), the same every year, or
"00-00&00-00" when it has none. The start is the first day on daylight time and the end
the first day back on standard time; a period may run across the new year, as in the
southern hemisphere ("10-04&04-04"). See clock.py for how the integration reads it.

Two text entities edit the two dates, as "MM-DD" (empty = not set). Writing one sends the
whole setting, with the other date as it is. The dates must be real days (February 29
included) and the start must differ from the end.

Both are unavailable while "General - Clock from Home Assistant" sets the clock.
"""

from __future__ import annotations

from datetime import date
import re

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GrowattThorError
from .clock import NO_DAYLIGHT_SAVING
from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity, check_owner

KEY = "G_DaylightSavingTime"
UNSET = "00-00"  # One half of NO_DAYLIGHT_SAVING.
_SETTING = re.compile(r"^(\d{2}-\d{2})&(\d{2}-\d{2})$")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Per charger: daylight saving start and end."""
    coordinator = entry.runtime_data
    async_add_entities(
        ThorDaylightSavingText(coordinator, sn, end)
        for sn in coordinator.data
        for end in (False, True)
    )


def _dates(setting: object) -> list[str]:
    """[start, end] of a G_DaylightSavingTime value; "00-00&00-00" when unreadable."""
    match = _SETTING.match(str(setting or ""))
    return list(match.groups()) if match else NO_DAYLIGHT_SAVING.split("&")


def _check_date(value: str) -> None:
    """Raise ServiceValidationError unless `value` is a real "MM-DD" day."""
    try:
        month, day = (int(part) for part in value.split("-"))
        date(2024, month, day)  # A leap year, so 02-29 is accepted.
    except ValueError as err:
        raise ServiceValidationError(f"{value} is not a day of the year (MM-DD)") from err


class ThorDaylightSavingText(ThorEntity, TextEntity):
    """The start or the end of the daylight saving period, as "MM-DD"."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 5
    _attr_pattern = r"^(\d{2}-\d{2})?$"

    def __init__(self, coordinator, sn: str, end: bool) -> None:
        super().__init__(coordinator, sn, "daylight_saving_end" if end else "daylight_saving_start")
        self._index = 1 if end else 0

    @property
    def available(self) -> bool:
        return super().available and self._sn not in self.coordinator.clock_sync

    @property
    def native_value(self) -> str | None:
        setting = self.charger.config.get(KEY)
        if setting is None:
            return None  # Not reported by the charger.
        value = _dates(setting)[self._index]
        return "" if value == UNSET else value

    async def async_set_value(self, value: str) -> None:
        """Write the whole setting with this date changed, then confirm with a refresh."""
        check_owner(self.charger)
        value = value.strip()
        if value:
            _check_date(value)
        dates = _dates(self.charger.config.get(KEY))
        dates[self._index] = value or UNSET
        if dates[0] == dates[1] and dates[0] != UNSET:
            raise ServiceValidationError("Daylight saving must start and end on different days")
        setting = "&".join(dates)
        try:
            await self.coordinator.api.async_set_config(self._sn, KEY, setting)
        except GrowattThorError as err:
            raise HomeAssistantError(f"Could not set daylight saving: {err}") from err
        self.charger.config[KEY] = setting
        # Both dates show the new setting.
        self.coordinator.async_update_listeners()
        await self.coordinator.async_refresh_after_write()
