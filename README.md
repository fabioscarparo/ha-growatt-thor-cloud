# Growatt THOR EV Charger for Home Assistant

Custom integration for Growatt THOR wallboxes, using Growatt's cloud service
(`evcharge.growatt.com`). The official Growatt integration covers inverters only.

## Tested with
- THOR 07AS-P-V1, firmware `THOR_07ASB-VA1.2.3.0-NOVO`

Other THOR models registered on a Growatt account should work, but have not been tested.

Requires Home Assistant 2025.3 or newer.

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
**Off-peak - ...**, **Boost ...** (PV Linkage and Off-peak), **Session - ...** and
**Advanced - ...**. Commands that do not apply to the current mode are shown as unavailable.

### Controls
| Entity | Type | Notes |
|---|---|---|
| Boost | switch | PV Linkage and Off-peak only |
| Charge mode | select | Fast / PV Linkage / Off-peak |
| Charging | switch | remote start / stop, no limit |
| Fast - Cancel scheduled start | button | available when a scheduled start exists |
| Fast - Start scheduled charge | button | Fast only |

### Sensors
| Entity | Type | Notes |
|---|---|---|
| Cable lock | binary sensor | on = unlocked |
| Current, Voltage | sensor | |
| Fast - Next scheduled start | timestamp | `every_day`, `limit`, `limit_value` attributes |
| Power | sensor, W | computed as voltage x current (single-phase) |
| Session - Cost, Duration, Energy | sensor | reset at each session |
| Session - Limit | enum | limit of the current session; value in the `value` attribute |
| Status | enum | connector status; a pending scheduled start reads as *Scheduled start* |
| Tariff | sensor | price of the charger's tariff slot in effect now; unknown if no slot covers now (outside a session) |

### Configuration
| Entity | Type | Notes |
|---|---|---|
| Advanced - ECO grid limit | number, disabled by default | low-level grid import for ECO, kW |
| Advanced - Solar mode | select, disabled by default | low-level FAST / ECO / ECO+ setting |
| Boost - Type | select | manual / smart (Off-peak is always smart) |
| Boost manual - From, To | time | full power window (PV Linkage only) |
| Boost smart - Departure time, Energy | time, number | energy guaranteed by that time |
| Fast - Limit | select | none / cost / energy / duration |
| Fast - Limit cost, duration, energy | number | value of the limit; duration in minutes |
| Fast - Start | select | now / at time / every day |
| Fast - Start at | time | time of a scheduled start |
| General - Authorization mode | select | APP/RFID / RFID / Plug & Charge |
| General - LCD display | switch | off = screen turns off automatically |
| General - Load balancing | switch | keeps the home's grid draw under the set limit |
| General - Max current | number | 6-32 A |
| General - Warm-up | switch | when the EV is full, keeps supplying power to preheat it in cold weather |
| Off-peak - Slot 1-3 from / to | time | off-peak slots; start = end leaves a slot unused |
| PV Linkage - Grid import power | number | kW, PV Linkage only: 0 = PV surplus only |

### Diagnostic
| Entity | Type | Notes |
|---|---|---|
| Error code, Vendor error code | sensor | |
| Grid sampling device, Meter type | sensor | CT or meter used by PV Linkage and load balancing |
| IP address | sensor, disabled by default | |
| Online | binary sensor | off when the status is Unavailable or not a known status |

### Charge modes
- **Fast**: charges at maximum power, from PV or grid. Can stop at a limit and start at a time
  (see *Scheduled charging*).
- **PV Linkage**: charges with PV surplus; needs a CT or meter. The minimum charging power is
  1.4 kW single-phase (4.1 kW three-phase). With *Grid import power* at 0 charging pauses when
  the surplus drops below it; with P kW the grid tops up to P kW to keep charging.
- **Off-peak**: charges only in the off-peak slots.

Switching mode from Home Assistant turns Boost off, and PV Linkage then starts without grid
import (set *PV Linkage - Grid import power* afterwards). PV Linkage needs a grid sampling
device (CT or meter) set on the charger.

**General** settings apply in every mode. Load balancing matters whenever the charger draws
from the grid: in Fast and Off-peak, and in PV Linkage with grid import or Boost; with PV
surplus only it has nothing to limit.

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

`start_charging` works in Fast only; with `every_day` a `start_time` is required, and a
`duration` limit is in minutes (at least 1). Values passed to an action are used as given and
do not change the dashboard settings.

- `growatt_thor_cloud.cancel_reservation`: cancel the scheduled start.
- `growatt_thor_cloud.set_boost`: `enabled`, `type` (manual/smart), `from`, `to`, `departure`,
  `energy`; missing values are taken from the Boost settings. The Boost entities follow what
  was sent.

## Polling and rate limits
Growatt's servers may rate limit frequent requests. The integration:
- polls every 60 s by default (*Configure* on the integration: 30-600 s), and reads the charger
  settings and the scheduled starts only every 5 minutes or right after a change made from
  Home Assistant (the scheduled starts also on every poll while one exists);
- logs in only when the session expires, one login at a time, and waits 5 minutes after a
  failed login before trying again;
- on errors or rate limiting keeps the last values for 5 minutes and slows polling down
  (2, 5, then 10 minutes), back to normal as soon as the cloud answers;
- retries the setup later if the cloud is unreachable at startup.

If Growatt rejects the login, Home Assistant asks for the password again (*Settings > Devices
& services*) and stops polling until then, so a wrong password never keeps retrying.

## Limitations
- Data is only as fresh as the Growatt cloud.
- Unofficial, undocumented API: Growatt can change it without notice.
- Single-connector chargers only.
- *Power* is voltage x current, exact for single-phase chargers only.
- Scheduled starts and tariff slots use Home Assistant's time zone, which must match the
  charger's.
- Chargers added to the account later appear after reloading the integration.

## Development
- [API_NOTES.md](API_NOTES.md): endpoints, payloads and field meanings.
- `tools/probe_thor.py`: dumps the raw API responses for your account (secrets redacted).
  Standard library only, no Home Assistant needed. Attach its output when reporting an
  unsupported charger.
  ```bash
  python3 tools/probe_thor.py
  ```
- Tests (config flow, entities, actions, polling behaviour and API client, against a mocked
  cloud):
  ```bash
  pip install -r requirements_test.txt
  pytest
  ```

## License
MIT, see [LICENSE](LICENSE).
