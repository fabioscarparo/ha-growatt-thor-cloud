"""Firmware: whether Growatt offers a newer firmware for the charger (read-only).

What it shows
-------------
One update entity per charger, "Firmware", with the firmware the charger runs and the
newest one Growatt offers for it. Home Assistant lists it under *Settings > Updates*
while a newer firmware is available:

- on: Growatt offers a newer firmware (`latest_version` is that version);
- off: the charger runs the newest firmware (`latest_version` equals the installed one);
- unknown: the check has not answered yet.

Where the data comes from
-------------------------
The `f_charger_version` command of `/ocpp/tcharg/tfirmware/` (see API_NOTES.md)
returns, for one charger:

    {"nowVersion": "...", "newVersion": "...", "needUpdate": ...}

`needUpdate` says whether `newVersion` is newer than `nowVersion`. Growatt sends it as
text ("false" while nothing newer is offered); it is read as yes when it is "true" or
"1", in any casing, also if it ever comes as a boolean or a number. Until the check
answers, the installed version falls back to the firmware `version` of the charger's
settings.

The coordinator runs the check at setup and then at most every few hours
(FIRMWARE_REFRESH_INTERVAL in coordinator.py): firmware releases are rare. A failed
check is not an error: the entity keeps the last answer.

Why it cannot install
---------------------
The cloud command that starts a firmware update is not known, so the entity offers no
*Install* button: chargers are updated with Growatt's own tools.
"""

from __future__ import annotations

from homeassistant.components.update import UpdateDeviceClass, UpdateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GrowattThorConfigEntry
from .entity import ThorEntity

# Values of `needUpdate` that mean a newer firmware is available.
NEED_UPDATE = ("true", "1")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrowattThorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """One read-only firmware update entity per charger found at setup."""
    coordinator = entry.runtime_data
    async_add_entities(ThorFirmwareUpdate(coordinator, sn) for sn in coordinator.data)


class ThorFirmwareUpdate(ThorEntity, UpdateEntity):
    """The charger's firmware and the newest one Growatt offers; no install (see above)."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator, sn: str) -> None:
        super().__init__(coordinator, sn, "firmware")

    @property
    def installed_version(self) -> str | None:
        """The firmware the charger runs: from the check, else from its settings."""
        if (charger := self.charger_or_none) is None:
            return None
        version = charger.firmware.get("nowVersion") or charger.config.get("version")
        return str(version) if version else None

    @property
    def latest_version(self) -> str | None:
        """The newer firmware when Growatt offers one, else the installed one.

        None (state unknown) until the check has answered: Home Assistant would
        otherwise read an empty answer as "up to date".
        """
        if (charger := self.charger_or_none) is None or not charger.firmware:
            return None
        need_update = str(charger.firmware.get("needUpdate") or "").lower() in NEED_UPDATE
        new_version = charger.firmware.get("newVersion")
        if need_update and new_version:
            return str(new_version)
        return self.installed_version
