# Growatt EV charger (THOR) cloud API

Notes on the cloud service behind the ShinePhone charger pages, as used by this integration.
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
- `userId` = prefix + ShinePhone account name. Prefix defaults to `SHINE`; the server may
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
  `cost` currency, **`rate` = tariff per kWh, not power**. No power field, so power = V x I.
  Also `status`, `transactionId`, `online` (0/1), `errorCode`, `vendorErrorCode`,
  `elockstate` (`locked`/`unlocked`).
- `configInfo` also contains secrets (`G_WifiPassword`, `G_CardPin`, `G_Authentication`):
  the integration drops them on read.
- `G_ChargerMode` (authorization): 1 = App, 2 = RFID, 3 = Plug&Charge (sent as int).
- `G_SolarMode`: 0 = FAST, 1 = ECO, 2 = ECO+ (sent as int).
- `G_MaxCurrent`: sent as string, minimum 3 A.
- `G_SolarLimitPower`: kW, sent as float.
- `G_ExternalLimitPowerEnable`: 0 = off, 1 = on (sent as int).
- `G_LCDCloseEnable`: `"Enable"` = screen turns off automatically, `"Disable"` = always on.
- `chargeMode.mode`: `fast`, `offPeak`, `pvLinkage` (+ `boostType` `manual`/`smart`). Changing it
  is `cmd: "update"` with the whole mode object (`G_PeriodTime`, `boost`, `config`, `importGrid`...).

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
