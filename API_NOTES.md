# Growatt EV charger (THOR) cloud API

Notes on Growatt's EV charger cloud service, as used by this integration.
Field meanings were checked against a real THOR 07AS-P-V1 (firmware `THOR_07ASB-VA1.2.3.0-NOVO`).

## Transport
- Base URL: `https://evcharge.growatt.com`. Some accounts may be served from another host,
  reported as `host` on `charger` entries of the smart-home device list (see Auth).
- All calls: `POST`, JSON body, header `Authorization: <token>` after login.
- Response: `{"code": 0, "data": ...}`; `code: 501` = not logged in, log in again.

## Auth
`POST /ocpp/user`
```json
{"cmd": "shineLogin", "userId": "SHINE<account>", "password": "<growatt_md5>", "lan": 1}
```
- `userId` = prefix + Growatt account name. Prefix defaults to `SHINE`; the server may
  override it via `prefix` on `charger` entries of `https://energy.growatt.com/room/`
  (`{"cmd":"devList","userId":...,"userServerUrl":...,"lan":...}`).
- `password` = MD5 hex where a single-digit byte is padded with `c` instead of `0`
  (same scheme as the inverter API).
- Response contains `token`, sent as `Authorization` header on every other call.
- Logout: `cmd: "shineLoginout"`.

## Read
| Endpoint | Body | Purpose |
|---|---|---|
| `/ocpp/api/list` | `userId, lan` | Chargers: `chargeId` (SN), `name`, `model`, `vendor`, `connectors`, `status_<n>`, `power` (W), `unit`, `symbol`, `priceConf[]`, `G_SolarMode`, `G_SolarLimitPower` |
| `/ocpp/charge/info` | `sn, connectorId, userId, lan` | Live connector data (see fields below) |
| `/ocpp/api/configInfo` | `sn, userId, lan` | Charger settings, network info, firmware `version`, `deviceModel` |
| `/ocpp/chargeMode` | `cmd:"select", chargeId, connectorId, userId` | Current charge mode |
| `/ocpp/api/chargeRecord` | - | Charge history |
| `/ocpp/api/` | `cmd:"noConfig"` etc. | Misc commands by `cmd` |

Field meanings:
- `charge/info`: `current` A, `voltage` V, `energy` kWh (session), `ctime` minutes,
  `cost` currency, `rate` = price applied to the running session (0 when idle, not power).
  No power field, so power = V x I.
  Also `status`, `transactionId`, `online` (0/1), `errorCode`, `vendorErrorCode`,
  `elockstate` (`locked`/`unlocked`).
- `configInfo` also contains secrets (`G_WifiPassword`, `G_CardPin`, `G_Authentication`):
  the integration drops them on read.
- Tariff: `priceConf` (in `list` and `configInfo`) = `[{"time": "HH:MM-HH:MM", "price": "0.21"}]`,
  one entry per time slot; slots may wrap past midnight. Set with `POST /ocpp/api/`
  `{"cmd":"addPrice","chargeId","priceConf":[{"time","price","name":""}],"userId","lan"}`.
- `G_ChargerMode` (authorization): 1 = APP/RFID, 2 = RFID, 3 = Plug&Charge (sent as int).
- `G_SolarMode`: 0 = FAST, 1 = ECO (PV surplus + grid import set by `G_SolarLimitPower`),
  2 = ECO+ (sent as int). ECO+ is not documented; it matches PV Linkage with grid import off.
  Low-level setting behind the charge modes: prefer `chargeMode`.
- `G_MaxCurrent`: sent as string, minimum 3 A.
- `G_SolarLimitPower`: kW, grid import used by ECO, sent as float.
- `G_ExternalLimitPowerEnable`: 0 = off, 1 = on (sent as int).
- `G_LCDCloseEnable`: `"Enable"` = screen turns off automatically, `"Disable"` = always on.
- `chargeMode.mode`: `fast`, `offPeak`, `pvLinkage`, as picked on the Growatt app charger screen.
  Other fields: `boost` (0/1), `boostType` (`manual`/`smart`), `config` (smart boost
  `contime=HH:MM&energy=<kWh>`), `importGrid` (kW), `G_PeriodTime` (off-peak slots).
- Boost: `boost` 1/0, `boostType` `manual` (PV Linkage only) with `config` =
  `"time1=HH:MM-HH:MM"` (full power in that window), or `smart` with `config` =
  `"contime=HH:MM&energy=<kWh>"` (energy guaranteed by that time).
- Grid sampling: `G_ExternalSamplingCurWring` 0 = CT 2000:1, 1 = meter, 2 = CT 3000:1;
  `G_PowerMeterType` = meter model (e.g. `Eastron SDM230`).
- PV Linkage needs a CT or meter. Minimum charging power: 1.4 kW single-phase, 4.1 kW three-phase.
  `importGrid` 0 = surplus only, charging pauses below the minimum; P kW = grid tops up to P.

Connector status values (OCPP): `Available, Preparing, Charging, SuspendedEV, SuspendedEVSE,
Finishing, Reserved, Unavailable, Faulted`.

## Write
- Start: `POST /ocpp/cmd/` `{"action":"remoteStartTransaction","chargeId","connectorId","userId","lan"}`
  (optional `cKey`/`cValue` preset limit, e.g. energy/cost/time).
- Stop: `POST /ocpp/cmd/` `{"action":"remoteStopTransaction","chargeId","connectorId","transactionId","userId","lan"}`
- Unlock: `POST /ocpp/api/` `{"cmd":"unlock","chargeId","connectorId","userId","lan"}`
- Settings: `POST /ocpp/api/config` `{"chargeId","userId","lan","<key>": value}` with keys like
  `G_MaxCurrent`, `G_ChargerMode`, `G_SolarMode`, `G_SolarLimitPower`, `G_ExternalLimitPower`,
  `G_ExternalLimitPowerEnable`, `G_PeakValleyEnable`, `G_AutoChargeTime`, `G_LCDCloseEnable`.
- Start with a limit: add `"cKey"` + `"cValue"` to `remoteStartTransaction`. Keys:
  `G_SetAmount` (cost, currency), `G_SetEnergy` (kWh), `G_SetTime` (duration in minutes; the app
  picks it as hours and minutes). `G_SetTime` also needs `"loopType": -1, "loopValue": "h:m"`
  (not zero-padded, e.g. `"1:30"`).
- Limited and scheduled starts are offered by the app in Fast mode only.
- Scheduled start: `POST /ocpp/cmd/` `{"action":"ReserveNow","expiryDate","connectorId","chargeId",
  "loopType","loopValue","userId","lan"}` plus optional `cKey`/`cValue`.
  `expiryDate` = `"YYYY-MM-DDTHH:MM:00.000Z"` in local time (the `Z` is literal, not UTC),
  `loopType` 0 = every day, -1 = once, `loopValue` = `"HH:MM"`.
- Reservations are listed in `charge/info` as a top-level `ReserveNow` array (next to `data`):
  `reservationId`, `expiryDate`, `loopType`, `loopValue`, `cKey`, `cValue`, `connectorId`.
  The running session limit is `data.cKey` / `data.cValue`.
- Cancel a reservation: `POST /ocpp/api/updateReserve` with the reservation fields (`cKey`,
  `cValue`, `connectorId`, `expiryDate`, `loopValue`, `loopType`, `reservationId`), `"sn"` and
  `"ctype": "2"`.
- Charge mode: `POST /ocpp/chargeMode` `{"cmd":"update","chargeId","connectorId","userId","lan","mode",...}`
  with the whole mode object:
  - `fast`: nothing else.
  - `pvLinkage`: `boost`, `boostType`, `config`, `importGrid`, plus the meter setup
    `G_ExternalSamplingCurWring` and `G_PowerMeterType` from `configInfo`.
  - `offPeak`: `boost`, `boostType`, `config`, `G_PeriodTime` = `"time1=HH:MM-HH:MM&time2=..."`,
    up to 5 slots in the app. Default slots are the cheapest `priceConf` entries. Only smart
    Boost exists in Off-peak.
