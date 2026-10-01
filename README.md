<p align="center">
  <img src="assets/icon.png" alt="Growatt THOR EV Charger" width="110">
</p>

<h1 align="center">Growatt THOR EV Charger for Home Assistant</h1>

<p align="center">
  <strong>Home Assistant integration for Growatt THOR wallboxes,<br>
  through Growatt's cloud service.</strong>
</p>

<p align="center">
  <a href="https://github.com/fabioscarparo/ha-growatt-thor-cloud/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/fabioscarparo/ha-growatt-thor-cloud?label=Release&color=5CC300"></a>
  <a href="https://hacs.xyz/"><img alt="HACS Custom" src="https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistantcommunitystore&logoColor=fff"></a>
  <a href="https://www.home-assistant.io/"><img alt="Home Assistant 2025.3+" src="https://img.shields.io/badge/Home_Assistant-2025.3%2B-18BCF2?logo=homeassistant&logoColor=fff"></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff"></a>
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/License-MIT-333"></a>
</p>

Custom integration for Growatt THOR wallboxes, using Growatt's cloud service
(`evcharge.growatt.com`). The official Growatt integration covers inverters only.

---

## Tested with
- THOR 07AS-P-V1, firmware `THOR_07ASB-VA1.2.3.0-NOVO`

Other THOR models registered on a Growatt account should work, but have not been tested.

Requires Home Assistant 2025.3 or newer; the integration's icon shows from Home Assistant
2026.3.

## Installation

### HACS (recommended)
1. In HACS open the menu (three dots, top right) > *Custom repositories*.
2. Add `https://github.com/fabioscarparo/ha-growatt-thor-cloud` with type *Integration*.
3. Search for **Growatt THOR EV Charger (Cloud)**, download it and restart Home Assistant.

### Manual
Copy `custom_components/growatt_thor_cloud` into your Home Assistant
`config/custom_components/` folder and restart Home Assistant.

### Setup
Add **Growatt THOR EV Charger (Cloud)** from *Settings > Devices & services > Add integration*
using your Growatt account username and password. Only the Growatt password hash is stored.
*Configure* on the integration sets the polling interval (see *Polling and rate limits*).

See [CHANGELOG.md](CHANGELOG.md) for what changed in each version.

## Entities
Home Assistant lists a device's entities alphabetically within each section, so names carry a
group prefix: **General - ...** (every mode), **Fast - ...**, **PV Linkage - ...**,
**Off-peak - ...**, **Boost ...** (PV Linkage and Off-peak), **Session - ...**, **Last
charge ...** and **Advanced - ...**. Commands that do not apply to the current mode are shown as unavailable.
Changes that are not allowed right now (see *During a session* and *RFID mode and shared
chargers*) are refused with a message, and the entities keep showing their values.

### Controls
| Entity | Type | Notes |
|---|---|---|
| Boost | switch | PV Linkage and Off-peak only |
| Charge mode | select | Fast / PV Linkage / Off-peak, as supported by the charger |
| Charging | switch | remote start / stop, no limit; refused in RFID mode |
| Fast - Cancel scheduled start | button | available when a scheduled start exists |
| Fast - Start scheduled charge | button | Fast only, outside a session |
| Unlock connector | button | unlocks the cable at the charger; available while no charge is in progress |

### Sensors
| Entity | Type | Notes |
|---|---|---|
| Cable lock | binary sensor | on = unlocked |
| Current, Voltage | sensor | |
| Fast - Next scheduled start | timestamp | `every_day`, `limit`, `limit_value` attributes |
| Last charge | timestamp | end of the last session |
| Last charge - Cost, Duration, Energy, Start | sensor | the last session, still shown once the session sensors reset |
| Power | sensor, W | computed as voltage x current (single-phase) |
| Session - Cost, Duration, Energy | sensor | reset at each session |
| Session - Limit | enum | limit of the current session; value in the `value` attribute |
| Session - Progress | sensor, % | how much of the session's limit, or of the smart Boost energy, is reached; unknown without one |
| Status | enum | connector status; a pending scheduled start reads as *Scheduled start* |
| Tariff | sensor | price of the charger's tariff slot in effect now; unknown if no slot covers now (outside a session) |

### Configuration
| Entity | Type | Notes |
|---|---|---|
| Advanced - Auto unlock connector | switch, disabled by default | installer setting: on = the charger unlocks the cable when it is unplugged from the EV |
| Advanced - ECO grid limit | number, disabled by default | low-level grid import for ECO, kW, available in ECO only; set by Growatt from *PV Linkage - Grid import power* |
| Advanced - LCD display | switch, disabled by default | chargers with a display only; installer setting: off = screen turns off automatically |
| Advanced - Solar mode | select, disabled by default | low-level FAST / ECO / ECO+ setting; set by Growatt from PV Linkage (ECO with grid import, ECO+ without) |
| Boost - Type | select | manual / smart (Off-peak is always smart) |
| Boost manual - From, To | time | full power window (PV Linkage only) |
| Boost smart - Departure time, Energy | time, number | energy guaranteed by that time |
| Fast - Limit | select | none / cost / energy / duration |
| Fast - Limit cost, duration, energy | number | value of the limit; duration in minutes |
| Fast - Start | select | now / at time / every day |
| Fast - Start at | time | time of a scheduled start |
| General - Authorization mode | select | APP/RFID / RFID / Plug & Charge |
| General - Load balancing | switch | keeps the home's grid draw under the set limit; unavailable in PV Linkage |
| General - Max current | number | 6-32 A; up to 16 A on 3.6 kW and 11 kW chargers |
| General - Warm-up | switch | when the EV is full, keeps supplying power to preheat it in cold weather |
| Off-peak - Slot 1-3 from / to | time | off-peak slots; start = end leaves a slot unused |
| PV Linkage - Grid import | switch | PV Linkage only: off = PV surplus only, on = the grid tops up the surplus |
| PV Linkage - Grid import power | number | kW: follows the charger while *Grid import* is on, also when changed in Growatt's settings, and keeps the last value while it is off |

### Diagnostic
| Entity | Type | Notes |
|---|---|---|
| Error code, Vendor error code | sensor | |
| Grid sampling device, Meter type | sensor | CT or meter used by PV Linkage and load balancing; the meter's bus address in the `address` attribute |
| IP address | sensor, disabled by default | |
| Network connection, Network mode | sensor | Wi-Fi or cable; DHCP or static address |
| Online | binary sensor | off when the status is Unavailable or not a known status |
| Protection temperature | sensor, °C | internal temperature at which the charger protects itself |
| Time zone | sensor | the charger's clock; daylight saving start and end (`MM-DD`) as attributes, see *Time zone* |
| Working mode | enum | the mode the charger runs, as it confirms it: Fast, PV Linkage with grid import or surplus only, Off-peak |

### Charge modes
- **Fast**: charges at maximum power, from PV or grid. Can stop at a limit and start at a time
  (see *Scheduled charging*).
- **PV Linkage**: charges with PV surplus; needs a CT or meter. The minimum charging power is
  1.4 kW single-phase (4.1 kW three-phase). With *Grid import* off, charging pauses when the
  surplus drops below the minimum. With it on at P kW (*Grid import power*): below the
  minimum, charging starts at the minimum once the surplus exceeds the minimum minus P; at or
  above the minimum, it starts right away at P. A larger surplus raises the power accordingly.
  The charger applies P in whole amps: 2 kW becomes 1.84 kW (8 A at 230 V).
- **Off-peak**: charges only in the off-peak slots.

*Charge mode* offers the modes the charger supports. Switching mode from Home Assistant turns
Boost off, and PV Linkage then starts without grid import (turn on *PV Linkage - Grid import*
afterwards). PV Linkage needs a grid sampling device (CT or meter) set on the charger.
After switching to PV Linkage or Off-peak, plug the cable in again if charging does not start
by itself.

**General** settings apply in every mode and can be changed at any time, also during a
session. *General - Load balancing* is not available in PV Linkage.

### During a session
While a session is open (charging, suspended or finishing), the charge mode and its settings
stay as they are until it ends. Changing *Charge mode*, *Boost* and its settings, *PV Linkage -
Grid import* and its power or the Off-peak slots is refused with a message, and *Fast - Start
scheduled charge* is unavailable. Settings that are only staged in Home Assistant (Boost and
grid import power while off, Off-peak slots outside Off-peak) can still be prepared.

### RFID mode and shared chargers
With *General - Authorization mode* set to RFID, sessions start and stop with a card: the
*Charging* switch and a Fast start *now* are refused, while scheduled starts are still sent.
On a charger shared with your account by its owner, settings and the charge mode cannot be
changed; starting and stopping still work.

### Scheduled charging (Fast)
Pick **Fast - Limit** (none, cost, energy or duration) and its value (**Fast - Limit cost**,
**duration** or **energy**), **Fast - Start** (now, at time, every day) and **Fast - Start at**,
then press **Fast - Start scheduled charge**. A start at a time becomes a scheduled start on the
charger, shown in **Fast - Next scheduled start** and removed with **Fast - Cancel scheduled
start**. Growatt allows one scheduled start per account at a time. A start time already passed
today is scheduled for tomorrow. Cost and energy limits must be above 0; a duration limit goes
from 1 minute to 23 h 59 min. These settings live in Home Assistant until you press the button
and are kept across restarts. Nothing is preset: the charger does not keep these values, so
they start empty (shown as unknown) and pressing the button with a missing value reports an
error.

### Off-peak slots
Up to 3 slots (**Off-peak - Slot n from / to**); a slot whose start equals its end, such as
00:00-00:00, is unused. While in Off-peak they show the charger's slots and changes are sent
right away; otherwise they are used the next time Off-peak is selected. Until you set them
they follow the last slots used, else the cheapest tariff slots, else they are unused, and
selecting Off-peak with no slot in use reports an error. Slots may not overlap; both ends
count, so a slot ending at 12:00 and one starting at 12:00 overlap. Slots beyond the third,
set outside Home Assistant (up to 5 in total), are kept when changing the first 3.

### Boost
In PV Linkage or Off-peak, **Boost** charges regardless of PV:
- **Manual** (PV Linkage only): full power between *Boost manual - From* and *To*.
- **Smart**: guarantees *Boost smart - Energy* by *Boost smart - Departure time*, using the
  grid if needed. Off-peak always uses smart Boost.

While Boost is on, its settings show what the charger runs and changes are sent right away.
Otherwise they start empty and must be set before turning Boost on.

### Actions
The same features are available as actions for automations and scripts:

```yaml
action: growatt_thor_cloud.start_charging
data:
  device_id: <charger device>
  limit: energy       # none, cost, energy or duration
  value: 20           # currency, kWh or minutes
  start_time: "23:00" # omit to start now
  every_day: true
```

`start_charging` works in Fast only and outside a session (in RFID mode only with a
`start_time`); with `every_day` a `start_time` is required, and a `duration` limit is in
minutes (at least 1). Values passed to an action are used as given and do not change the
dashboard settings.

- `growatt_thor_cloud.cancel_reservation`: cancel the scheduled start.
- `growatt_thor_cloud.set_boost`: `enabled`, `type` (manual/smart), `from`, `to`, `departure`,
  `energy`; missing values are taken from the Boost settings. The Boost entities follow what
  was sent. Outside a session only.

## Polling and rate limits
Growatt's servers may rate limit frequent requests. The integration:
- polls every 60 s by default (*Configure* on the integration: 30-600 s), and reads the charger
  settings, the scheduled starts and the charge history only every 5 minutes (the scheduled
  starts also on every poll while one exists and right after a change, the history also as
  soon as a session ends);
- after a change made from Home Assistant, shows the new value right away and reads the
  settings again about 2 minutes later, once the charger has applied it (it takes about a
  minute): reading them sooner would bring back the old value;
- logs in only when the session expires, one login at a time, and waits 5 minutes after a
  failed login before trying again;
- on errors or rate limiting keeps the last values for 5 minutes and slows polling down
  (2, 5, then 10 minutes), back to normal as soon as the cloud answers;
- retries the setup later if the cloud is unreachable at startup.

If Growatt rejects the login, Home Assistant asks for the password again (*Settings > Devices
& services*) and stops polling until then, so a wrong password never keeps retrying.

## Troubleshooting
- An action that fails or is not allowed shows its reason in a message right away.
- Cloud and connection problems are logged in *Settings > System > Logs*.
- For more detail, turn on *Enable debug logging* in the integration's menu (*Settings >
  Devices & services > Growatt THOR EV Charger (Cloud)*), reproduce the problem, then turn it
  off: Home Assistant downloads the log. It lists every request to Growatt's cloud and its
  reply, with credentials, the session token and the Wi-Fi name masked; it still contains
  the account name and the serial number.

## Time zone
Off-peak slots, Boost windows and scheduled starts run on the charger's own clock: a time zone
such as UTC+1, plus a daylight saving period set by date for one year at a time. The *Time
zone* sensor shows both. When the charger's clock differs from Home Assistant's, a warning
appears in *Settings > System > Repairs*, since those times would run early or late.

Set the charger's time zone and daylight saving period in its Growatt settings (*Basic
information*), and renew the daylight saving dates every year. In central Europe, for
example: UTC+1 with daylight saving from the last Sunday of March to the last Sunday of
October (03-29 to 10-25 in 2026). On the charger's own switch days the warning is left as it
is, since the hour of the switch is not known.

## Limitations
- Data is only as fresh as the Growatt cloud.
- Unofficial, undocumented API: Growatt can change it without notice.
- Single-connector chargers only.
- *Power* is voltage x current, exact for single-phase chargers only.
- Scheduled starts and the current tariff slot are worked out in Home Assistant's time zone,
  which must match the charger's clock (see *Time zone*).
- Chargers added to the account later appear after reloading the integration.

## Development
- [API_NOTES.md](API_NOTES.md): endpoints, payloads and field meanings.
- `tools/probe_thor.py`: dumps the raw API responses for your account: chargers, settings,
  live data, scheduled starts, charge mode, installer-protected settings, time-slot power
  limits, the last sessions and the time zone list. Credentials are redacted and personal
  data (account name, serial numbers, network details, site) is masked. Standard library
  only, no Home Assistant needed. Attach its output when reporting an unsupported charger.
  ```bash
  python3 tools/probe_thor.py
  ```
- Tests (config flow, entities, actions, change rules, clock warning, polling behaviour and
  API client, against a mocked cloud):
  ```bash
  pip install -r requirements_test.txt
  pytest
  ```

## Note
This is an unofficial project: it is **not affiliated with, endorsed by, or developed by
Growatt**.

## License
MIT, see [LICENSE](LICENSE).
