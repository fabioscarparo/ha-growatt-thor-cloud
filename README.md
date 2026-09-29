# Growatt THOR EV Charger for Home Assistant

Custom integration for Growatt THOR wallboxes, using the same cloud service as the
ShinePhone app (`evcharge.growatt.com`). The official Growatt integration covers
inverters only.

## Tested with
- THOR 07AS-P-V1, firmware `THOR_07ASB-VA1.2.3.0-NOVO`

Other THOR models registered in ShinePhone should work, but have not been tested.

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
using your ShinePhone username and password. Only the Growatt password hash is stored.

## Entities
| Entity | Type | Notes |
|---|---|---|
| Status | sensor (enum) | OCPP connector status |
| Charge mode | sensor (enum) | fast / off-peak / PV linkage |
| Power | sensor, W | computed as voltage x current (single-phase) |
| Current, Voltage | sensor | |
| Session energy / duration / cost | sensor | reset at each session |
| Tariff | sensor | price per kWh configured in ShinePhone |
| Error code, Vendor error code, IP | diagnostic | |
| Online | binary sensor | cloud connection of the charger |
| Cable lock | binary sensor | on = unlocked |
| Charging | switch | remote start / stop |
| Load balancing | switch | dynamic load balancing with the external meter |
| LCD display | switch | off = screen turns off automatically |
| Max current | number | 6-32 A |
| Solar limit power | number | kW, PV linkage threshold / allowed grid import |
| Solar mode | select | FAST / ECO / ECO+ (no PV, PV linkage, PV linkage+) |
| Authorization mode | select | App / RFID / Plug & Charge |

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
