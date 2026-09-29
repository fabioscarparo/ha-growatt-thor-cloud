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

## Entities
| Entity | Type | Notes |
|---|---|---|
| Status | sensor (enum) | OCPP connector status |
| Power | sensor, W | computed as voltage x current (single-phase) |
| Current, Voltage | sensor | |
| Session energy / duration / cost | sensor | reset at each session |
| Tariff | sensor | price of the current time slot configured in the Growatt app |
| Session limit | sensor (enum) | limit of the current session; value in the `value` attribute |
| Next reservation | sensor, timestamp | next scheduled start; `every_day`, `limit` attributes |
| Error code, Vendor error code, IP | diagnostic | |
| Grid sampling device, Meter type | diagnostic | CT or meter used by PV Linkage / load balancing |
| Online | binary sensor | cloud connection of the charger |
| Cable lock | binary sensor | on = unlocked |
| Charging | switch | remote start / stop, no limit |
| Boost | switch | PV Linkage / Off-peak, uses the Boost settings below |
| Load balancing | switch | dynamic load balancing with the external meter |
| LCD display | switch | off = screen turns off automatically |
| Charge mode | select | Fast / PV Linkage / Off-peak, see below |
| Grid import power | number | kW, PV Linkage only: 0 = PV surplus only |
| Max current | number | 6-32 A |
| Authorization mode | select | APP/RFID / RFID / Plug & Charge |
| Start scheduled charge, Cancel reservation | button | send the scheduled charge settings below |
| Charge limit, Cost / Energy / Duration limit, Start, Start time | config | scheduled charge settings |
| Boost type, Boost from / to, Boost departure time, Boost energy | config | Boost settings |
| Solar mode | select, disabled by default | low-level FAST / ECO / ECO+ setting |
| ECO grid limit | number, disabled by default | low-level grid import for ECO, kW |

### Charge modes
- **Fast**: charges at maximum power, from PV or grid.
- **PV Linkage**: charges with PV surplus; needs a CT or meter. The minimum charging power is
  1.4 kW single-phase (4.1 kW three-phase). With *Grid import power* at 0 charging pauses when
  the surplus drops below it; with P kW the grid tops up to P kW to keep charging.
- **Off-peak**: charges only in the off-peak time slots. Uses the slots chosen in the Growatt app,
  or the cheapest tariff slots if none were chosen; tariffs must be set in the Growatt app first.

Switching mode from Home Assistant turns Boost off.

### Scheduled charging
Pick a **Charge limit** (none, cost, energy or duration) and its value, a **Start** (now, at
time, every day) and a **Start time**, then press **Start scheduled charge**. A start at a time
becomes a reservation on the charger, shown in **Next reservation** and removed with
**Cancel reservation**. These settings live in Home Assistant until you press the button and
are kept across restarts.

### Boost
In PV Linkage or Off-peak, **Boost** charges regardless of PV:
- **Manual** (PV Linkage only): full power between *Boost from* and *Boost to*.
- **Smart**: guarantees *Boost energy* by *Boost departure time*, using the grid if needed.

While Boost is on, its settings show what the charger runs and changes are sent right away.

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

- `growatt_thor_cloud.cancel_reservation`: cancel the scheduled starts.
- `growatt_thor_cloud.set_boost`: `enabled`, `type` (manual/smart), `from`, `to`, `departure`, `energy`.

## Polling and rate limits
Growatt's cloud limits how often it can be queried. The integration:
- polls every 60 s by default (*Configure* on the integration: 30-600 s), and reads the charger
  settings only every 5 minutes or right after a change made from Home Assistant;
- logs in only when the session expires, one login at a time, and waits 5 minutes after a
  failed login before trying again;
- on errors or rate limiting keeps the last values for 5 minutes and slows polling down
  (2, 5, then 10 minutes), back to normal as soon as the cloud answers;
- retries the setup later if the cloud is unreachable at startup.

## Limitations
- Data is only as fresh as the Growatt cloud.
- Unofficial, undocumented API: Growatt can change it without notice.
- Single-connector chargers only.

## Development
- [API_NOTES.md](API_NOTES.md): endpoints, payloads and field meanings.
- `tools/probe_thor.py`: dumps the raw API responses for your account (secrets redacted).
  Standard library only, no Home Assistant needed. Attach its output when reporting an
  unsupported charger.
  ```bash
  python3 tools/probe_thor.py
  ```
- Tests (config flow, entities, commands and API client, against a mocked cloud):
  ```bash
  pip install -r requirements_test.txt
  pytest
  ```

## License
MIT, see [LICENSE](LICENSE).
