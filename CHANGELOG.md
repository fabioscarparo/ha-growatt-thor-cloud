# Changelog

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
