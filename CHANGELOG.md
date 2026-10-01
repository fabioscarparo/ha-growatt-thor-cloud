# Changelog

## 0.6.3
### Changed
- *Advanced - ECO grid limit* is available only while *Advanced - Solar mode* is ECO, the
  only mode that uses it.

## 0.6.2
### New
- *Working mode* (diagnostic): the mode the charger actually runs, as it confirms it, e.g.
  PV Linkage with grid import or surplus only.

### Changed
- Settings are read once more about 2 minutes after a change made from Home Assistant, once
  the charger has confirmed it (it takes about a minute), instead of up to 5 minutes later.
- With debug logging enabled, every request to Growatt's cloud and its reply is logged,
  with credentials, the session token and the Wi-Fi name masked, to diagnose commands the
  charger rejects.
- README: a *Troubleshooting* section, and *PV Linkage - Grid import power* follows the
  charger while grid import is on, also when changed in Growatt's settings.

## 0.6.1
### New
- *PV Linkage - Grid import*: turns grid import on (at *PV Linkage - Grid import power*) or
  off (PV surplus only). The power is kept in Home Assistant while grid import is off, and
  is sent right away while it is on.

### Changed
- The last session has its own entities: *Last charge* (end), *Last charge - Start*,
  *Duration*, *Energy* and *Cost*, instead of attributes of *Session - Last charge*.

## 0.6.0
### New
- *Unlock connector*: unlocks the cable at the charger while no charge is in progress.
- *Advanced - Auto unlock connector* (disabled by default): the charger unlocks the cable
  once it is unplugged from the EV.
- *Session - Progress*: how much of the session's limit, or of the smart Boost energy, is
  reached.
- *Session - Last charge*: end of the last session, with its start, duration, energy and
  cost; the session sensors reset once a session is over.
- Diagnostics: *Time zone* (with the daylight saving period), *Network connection*, *Network
  mode*, *Protection temperature*, and the meter's bus address on *Meter type*.
- A warning in Repairs while the charger's clock differs from Home Assistant's: Off-peak
  slots, Boost windows and scheduled starts would run at the wrong time.
- `tools/probe_thor.py` also dumps the installer-protected settings, the time-slot power
  limits, the last sessions and the time zone list, and masks personal data (account name,
  serial numbers, network details, site) so its output can be attached to an issue.

### Changed
- While a session is open (charging, suspended or finishing), the charge mode, Boost, the grid
  import, the Off-peak slots and Fast limits and scheduled starts can no longer be changed;
  the change is refused with a message. General settings can still change at any time.
- In RFID authorization mode, remote start and stop are refused (scheduled starts are still
  sent).
- *General - Load balancing* is unavailable in PV Linkage.
- *Charge mode* offers only the modes the charger supports.
- On a charger shared with the account, settings and the charge mode are read-only.
- *General - Max current* goes up to 16 A on 3.6 kW and 11 kW chargers.
- *LCD display* is now *Advanced - LCD display*, an installer setting disabled for new
  installs, and exists only on chargers with a display (it is removed from the others).
- When no charger is found during setup, the message suggests checking the username.

### Fixed
- The result of start, stop and scheduled start commands is read from `type` as well as
  `code`, so a command the charger rejects is reported as an error.
- An invalid grid import (e.g. without a grid sampling device) is reported as a validation
  error instead of an unexpected one.

## 0.5.3
### Changed
- The integration icon has rounded corners.

## 0.5.2
### New
- Integration icon, shown by Home Assistant 2026.3 or newer.
- README header with icon and badges.

## 0.5.1
### Changed
- In Italian, Boost is shown as "Boost" again (it was "Incremento" in 0.5.0).

## 0.5.0
### New
- *General - Warm-up*: once the EV is full, the charger keeps supplying power so it can
  preheat in cold weather.

### Changed
- Entity names are grouped so related entities sit together on the device page:
  *General* (every mode), *Fast*, *PV Linkage*, *Off-peak*, *Boost* (manual / smart),
  *Session* and *Advanced*. Existing entity ids are unchanged.
- "Reservation" is now called "scheduled start" in entity names, the status and the
  `cancel_reservation` action (its id is unchanged).
- In Italian, Boost is shown as "Incremento".

## 0.4.2
### Fixed
- Reservations are read from the reservation list (`/ocpp/api/ReserveNow`), while one is
  pending or listed and with the settings otherwise, and right after scheduling or cancelling;
  if the list cannot be read, the last one is kept and the rest of the data still updates.
  *Next reservation* shows the reservation's displayed limit value.
- Status: the reservation states `Accepted` and `ReserveNow` now read as Reserved instead of
  unknown.
- Online now follows the status (off when Unavailable or unknown) instead of a cloud flag
  whose meaning is unverified.
- Switching mode now starts PV Linkage with Boost off, manual Boost type and no grid import,
  and Off-peak always with the smart Boost type, instead of reusing values from the previous
  mode. PV Linkage without a grid sampling device is refused.
- Off-peak slots that overlap, including slots sharing a start/end minute, are refused.
- Cost and energy limits accept any value above 0 (were 0.5 minimum, 500 / 200 maximum).
- Tariff is unknown when no tariff slot covers the current time outside a session, instead
  of showing 0.
- Re-entering the password no longer reloads the integration twice (two logins in a few
  seconds, which Growatt may rate limit). Only a new polling interval reloads it.
- Starting and stopping a charge no longer re-reads the charger settings.
- A malformed charger entry from the cloud is skipped instead of failing the whole update.
- A duration limit under 1 minute is rejected instead of being sent as 0 minutes.
- An unreadable saved setting starts empty instead of breaking the entity.

## 0.4.1
### Fixed
- Limit, start time and Boost settings no longer show made-up values: the charger does not
  keep them, so they start empty until you set them. Using a value that was never set reports
  an error instead of sending a default.
- Values saved by previous versions are discarded once after updating.
- Off-peak slots no longer fall back to a made-up 23:00-07:00 slot.

## 0.4.0
### New
- Off-peak slots: up to 3 (*Off-peak - Slot n from / to*); a slot whose start equals its end
  is unused. Sent at once while in Off-peak, otherwise used when switching to it. Slots beyond
  the third, set outside Home Assistant, are kept.

### Changed
- Settings are grouped by name: *Fast*, *PV Linkage*, *Off-peak*, *Boost*, *Advanced*.
  Existing entity ids are unchanged.
- Commands that do not apply to the current mode are unavailable. Scheduled charging works
  in Fast only.
- Off-peak always uses smart Boost.

## 0.3.0
### New
- Scheduled charging: stop at a cost, energy or duration limit; start now, at a time or every
  day; cancel reservations. As entities and as the `start_charging` and `cancel_reservation`
  actions.
- Boost in PV Linkage and Off-peak (manual window or smart energy by a departure time), as a
  switch with its settings and as the `set_boost` action.
- Sensors: Session limit, Next reservation, Grid sampling device, Meter type.
- Polling interval option (30-600 s).

### Changed
- Gentler on Growatt's cloud: one login at a time with a 5-minute pause after a failed login,
  settings read every 5 minutes, last values kept for 5 minutes on errors or rate limiting
  while polling slows down.

## 0.2.0
### New
- Charge mode is selectable: Fast, PV Linkage or Off-peak.
- Grid import power for PV Linkage (0 = PV surplus only).

### Changed
- The first authorization mode option is now labelled "APP/RFID", as in the THOR manual.
- Solar mode (FAST / ECO / ECO+) and ECO grid limit are disabled by default for new
  installations.

### Upgrading
- The old Charge mode sensor is replaced by the Charge mode select: remove the leftover
  sensor from *Settings > Entities*.

## 0.1.1
### Fixed
- Tariff showed 0 when not charging; it now reads the price of the current time slot.

## 0.1.0
- First release: charger status, power, current, voltage, session energy / duration / cost,
  tariff, online and cable lock; remote start / stop; max current, load balancing, LCD
  display, solar mode and authorization mode.
