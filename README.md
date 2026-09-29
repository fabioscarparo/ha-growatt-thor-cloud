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
| Error code, Vendor error code, IP | diagnostic | |
| Online | binary sensor | cloud connection of the charger |
| Cable lock | binary sensor | on = unlocked |
| Charging | switch | remote start / stop |
| Load balancing | switch | dynamic load balancing with the external meter |
| LCD display | switch | off = screen turns off automatically |
| Charge mode | select | Fast / PV Linkage / Off-peak, see below |
| Grid import power | number | kW, PV Linkage only: 0 = PV surplus only |
| Max current | number | 6-32 A |
| Authorization mode | select | APP/RFID / RFID / Plug & Charge |
| Solar mode | select, disabled by default | low-level FAST / ECO / ECO+ setting |
| ECO grid limit | number, disabled by default | low-level grid import for ECO, kW |

### Charge modes
- **Fast**: charges at maximum power, from PV or grid.
- **PV Linkage**: charges with PV surplus; needs a CT or meter. The minimum charging power is
  1.4 kW single-phase (4.1 kW three-phase). With *Grid import power* at 0 charging pauses when
  the surplus drops below it; with P kW the grid tops up to P kW to keep charging.
- **Off-peak**: charges only in the off-peak time slots. Uses the slots chosen in the Growatt app,
  or the cheapest tariff slots if none were chosen; tariffs must be set in the Growatt app first.

Boost (manual or smart) is configured in the Growatt app; switching mode from Home Assistant turns it off.

## Limitations
- Cloud polling every 60 s; data is only as fresh as the Growatt cloud.
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
