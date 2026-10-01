# Growatt EV charger (THOR) cloud API

Notes on Growatt's EV charger cloud service, as used by this integration.
Field meanings were checked against a real THOR 07AS-P-V1 (firmware
`THOR_07ASB-VA1.2.3.0-NOVO`).

## Transport
- Base URL: `https://evcharge.growatt.com`. Some accounts may be served from another host,
  reported as `host` on `charger` entries of the smart-home device list (see Auth).
- All calls: `POST`, JSON body, header `Authorization: <token>` after login.
- Response: `{"code": 0, "data": ...}`; `code: 501` = not logged in, log in again. Other
  non-zero codes are errors; their meanings are not documented. Commands (`/ocpp/cmd/`) carry
  their result in `type` instead (0 = done, 501 = not logged in), with or without `code`.
- `lan` selects the language of messages: 1 = English.

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
| `/ocpp/charge/info` | `sn, connectorId (int), userId, lan` | Live connector data (see fields below) |
| `/ocpp/api/ReserveNow` | `chargeId, connectorId (string), userId, lan` | Reservations (scheduled starts) of the connector (see Write) |
| `/ocpp/api/configInfo` | `sn, userId, lan` | Charger settings, network info, firmware `version`, `deviceModel` |
| `/ocpp/chargeMode` | `cmd:"select", chargeId, connectorId (int), userId` | Current charge mode |
| `/ocpp/api/chargeRecord` | `sn, page, psize, userId, lan` | Sessions, newest first (see below) |
| `/ocpp/meterInfo` | `cmd:"meterInfo", chargeId, lan` | `data` = power measured by the CT or meter, W |
| `/ocpp/api/timeZoneList2` | `{}` | Time zones for `sysTimeZone` |
| `/ocpp/tcharg/tfirmware/` | `cmd:"f_charger_version", chargeId, lan` | `data[0]`: `nowVersion`, `newVersion`, `needUpdate` |
| `/ocpp/api/` | `cmd` + fields | Misc commands by `cmd`, below |

`/ocpp/api/` commands:
- `noConfig` (`userId, lan`): `sfield` = settings protected by an installer password, which
  comes in the same reply (`configWord`, `password`); never print or store it.
- `selectLimitPower` (`chargeId`): power limits by time slot, `isEnable` (1/0), `cid` and
  `config[]` of `{"loop": "1111111", "time": "HH:MM-HH:MM", "power": "<kW>"}`, one `loop`
  flag per weekday, up to 10 slots. Written with `updateLimitPower` (`isEnable`, `cid`,
  `config`).
- `chargeData` (`chargeId, timeType, time, requestType:"0"`): energy and cost per period,
  `data[]` of `{t, energy, cost}`; `timeType` 0 = days of a month (`time` `YYYY-MM`), 1 = months
  of a year (`YYYY`), 2 = years.
- `unlock`, `addPrice`: see Write.

`chargeRecord` entries: `starttime` / `endtime` (`"YYYY-MM-DD HH:MM:SS"` on the charger's
clock), `ctime` (minutes), `energy` (kWh), `cost`, `chargemode` (authorization used: 1 =
APP, 2 = RFID, 3 = Plug&Charge), `userId` (idTag), `transactionId`. `sysStartTime` /
`sysEndTime` are those wall-clock times read as UTC+8, not true epochs. `pvEnergy` and
`consume` were 0 in every entry seen. The live data of `charge/info` goes back to 0 once a
session is over.

Field meanings:
- `charge/info` `data`: `current` A, `voltage` V, `energy` kWh (session), `ctime` minutes,
  `cost` currency, `rate` = price applied to the running session (0 when idle, not power).
  No power field, so power = V x I. Also `status`, `transactionId` (0 = none), `errorCode`,
  `vendorErrorCode`, `elockstate` (`locked`/`unlocked`), and the running session limit
  `cKey` / `cValue`. The `online` flag is not used: its meaning is unverified. The response may
  also carry `ReserveNow` and `LastAction` next to `data`; they are not used either.
- `status`: the OCPP values `Available`, `Preparing`, `Charging`, `SuspendedEV`,
  `SuspendedEVSE`, `Finishing`, `Reserved`, `Unavailable`, `Faulted`, plus `Accepted` and
  `ReserveNow` (a reservation is pending, same as `Reserved`) and `None` (still loading).
  Other values are unknown; the integration's Online sensor treats them as offline.
- `configInfo` also contains secrets (`G_WifiPassword`, `G_CardPin`, `G_Authentication`,
  `G_4GPassword`, `G_4GUserName`): the integration drops them on read.
- `list` entries: `type` 1 = charger shared with the account by its owner (its settings and
  charge mode cannot be changed, starting and stopping can), 0 = own charger.
- Feature flags in `configInfo`: `isSupportPL` (PV Linkage), `isSupportLoadBalancing`,
  `isSupportLowRateMode` (off-peak), `isSupportRF`, `isSupport_LCDEnable` (false on models
  without a display). A charger with neither load balancing nor low-rate support runs Fast
  only; PV Linkage also needs `isSupportPL`. Missing flags are taken as supported.
- `noConfig` lists among the protected (installer) settings `G_LCDCloseEnable`,
  `UnlockConnectorOnEVSideDisconnect`, `G_MaxTemperature`, `G_RCDProtection`,
  `G_PowerMeterType` and `G_PowerMeterAddr`; `sysTimeZone` and `G_DaylightSavingTime` are not
  protected.
- Clock: `sysTimeZone` (e.g. `UTC+2`, from `timeZoneList2`) plus `G_DaylightSavingTime` =
  `"MM-DD&MM-DD"`, the daylight saving start and end for one year (`00-00&00-00` = not set).
  Off-peak slots, Boost windows and scheduled starts run on this clock.
- `G_NetType` (`wifi` / `cable`), `G_NetworkMode` (`DHCP` / `STATIC`), `G_MaxTemperature`
  (protection temperature, °C), `G_PowerMeterAddr` (meter bus address), `G_RCDProtection`
  (protection level 1-9).
- `G_AutoChargeTime`: window in which charging is allowed, `"HH:MM-HH:MM"`, empty = always.
- `G_RandDelayChargeTime`: random delay before a session starts, s (0 = off, 600 by default,
  1-1800).
- `G_ExternalLimitPower`: highest grid import for load balancing, kW.
- `UnlockConnectorOnEVSideDisconnect`: `"true"` = the cable is unlocked at the charger once it
  is unplugged from the EV, `"false"` = it stays locked (sent as string).
- Tariff: `priceConf` (in `list` and `configInfo`) = `[{"time": "HH:MM-HH:MM", "price": "0.21"}]`,
  one entry per time slot; slots may wrap past midnight. Set with `POST /ocpp/api/`
  `{"cmd":"addPrice","chargeId","priceConf":[{"time","price","name":""}],"userId","lan"}`.
- `G_ChargerMode` (authorization): 1 = APP/RFID, 2 = RFID, 3 = Plug&Charge (sent as int).
  In RFID mode sessions start and stop with a card, not remotely.
- `G_SolarMode`: 0 = FAST, 1 = ECO (PV surplus + grid import set by `G_SolarLimitPower`),
  2 = ECO+ (sent as int). ECO+ is not documented; it appears to match PV Linkage with grid
  import off. Low-level setting behind the charge modes: prefer `chargeMode`.
- `G_MaxCurrent`: A, sent as string.
- `G_SolarLimitPower`: kW, grid import used by ECO, sent as float.
- Growatt sets `G_SolarMode` and `G_SolarLimitPower` from the PV Linkage `importGrid`: ECO with
  the limit rounded down to whole amps (2 kW -> 1.84 kW, 8 A at 230 V) while it is above 0,
  ECO+ when it is 0 (the limit then keeps its last value). The charger confirms them about a
  minute after the mode update; `ctime` in `configInfo` and in `chargeMode` is the time of the
  last update (epoch ms).
- `G_WorkingMode`: the mode the charger runs: `Fast`, `PVlink` (PV Linkage with grid import),
  `PVlink+` (surplus only), `Off Peak`, `Power Distribution`, with a ` ManualBoost` /
  ` SmartBoost` suffix while Boost runs.
- `G_ExternalLimitPowerEnable`: 0 = off, 1 = on (sent as int).
- `G_LCDCloseEnable`: `"Enable"` = screen turns off automatically, `"Disable"` = always on.
- `G_FullContinueChargeEnable` (warm-up): `"Enable"` = once the EV is full, keep supplying
  power so it can preheat in cold weather; `"Disable"` = off.
- `chargeMode.mode`: `fast`, `offPeak`, `pvLinkage` (the charger's working mode). Other
  fields: `boost` (0/1), `boostType` (`manual`/`smart`), `config` (Boost settings, see below),
  `importGrid` (kW), `G_PeriodTime` (off-peak slots).
- Boost: `boost` 1/0, `boostType` `manual` (PV Linkage only) with `config` =
  `"time1=HH:MM-HH:MM"` (full power in that window), or `smart` with `config` =
  `"contime=HH:MM&energy=<kWh>"` (energy guaranteed by that time); times are zero-padded.
  With Boost off, `config` is `""`.
- Grid sampling: `G_ExternalSamplingCurWring` 0 = CT 2000:1, 1 = meter, 2 = CT 3000:1
  (-1 or missing = not set); `G_PowerMeterType` = meter model (e.g. `Eastron SDM230`).
- PV Linkage needs a CT or meter. Minimum charging power: 1.4 kW single-phase, 4.1 kW
  three-phase. `importGrid` 0 = surplus only, charging pauses below the minimum; P kW = grid
  tops up to P. There is no separate on/off field for grid import.

## Write
- Start: `POST /ocpp/cmd/` `{"action":"remoteStartTransaction","chargeId","connectorId","userId","lan"}`.
- Stop: `POST /ocpp/cmd/` `{"action":"remoteStopTransaction","chargeId","connectorId","transactionId","userId","lan"}`.
- Unlock: `POST /ocpp/api/` `{"cmd":"unlock","chargeId","connectorId","userId","lan"}`, with
  `connectorId` as string; meant for when no charge is in progress.
- Settings: `POST /ocpp/api/config` `{"chargeId","userId","lan","<key>": value}` with keys like
  `G_MaxCurrent`, `G_ChargerMode`, `G_SolarMode`, `G_SolarLimitPower`, `G_ExternalLimitPower`,
  `G_ExternalLimitPowerEnable`, `G_PeakValleyEnable`, `G_AutoChargeTime`, `G_LCDCloseEnable`,
  `G_FullContinueChargeEnable`, `UnlockConnectorOnEVSideDisconnect`, `G_RandDelayChargeTime`,
  `sysTimeZone`, `G_DaylightSavingTime`. These can change at any time, also during a session.
- The charge mode, its Boost and slots, and Fast limits and scheduled starts are changed only
  outside a session (`Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing`): stop the session
  before switching mode.
- Limited and scheduled starts belong to Fast mode.
- Start with a limit: add `"cKey"` + `"cValue"` (string) to `remoteStartTransaction`. Keys:
  `G_SetAmount` (cost, currency, above 0), `G_SetEnergy` (kWh, above 0), `G_SetTime` (duration
  in minutes, up to 23 h 59 min). `G_SetTime` also needs `"loopType": -1, "loopValue": "h:m"`
  (not zero-padded, e.g. `"1:30"`).
- Scheduled start: `POST /ocpp/cmd/` `{"action":"ReserveNow","expiryDate","connectorId","chargeId",
  "loopType","loopValue","userId","lan"}` plus optional `cKey`/`cValue`.
  `expiryDate` = `"YYYY-MM-DDTHH:MM:00.000Z"` in local time (the `Z` is literal, not UTC),
  `loopType` 0 = every day, -1 = once, `loopValue` = `"HH:MM"`. The integration uses the next
  occurrence of the time (tomorrow if already passed today). One scheduled start per account
  at a time.
- Reservations: `/ocpp/api/ReserveNow` returns `data[]` with `reservationId`, `expiryDate`,
  `loopType`, `loopValue`, `cKey`, `cValue`, `cValue2` (value to display), `connectorId`,
  `status`, `rate`, `cost`.
- Cancel a reservation: `POST /ocpp/api/updateReserve` with the list entry's `cKey`, `cValue`,
  `connectorId`, `expiryDate`, `loopValue`, `loopType`, `reservationId`, plus `"sn"` and
  `"ctype": "2"`; one request per reservation.
- Charge mode: `POST /ocpp/chargeMode` `{"cmd":"update","chargeId","connectorId","userId","lan","mode",...}`
  with the whole mode object:
  - `fast`: nothing else.
  - `pvLinkage`: `boost`, `boostType`, `config`, `importGrid`, plus the meter setup
    `G_ExternalSamplingCurWring` (as string) and `G_PowerMeterType` from `configInfo`.
  - `offPeak`: `boost`, `boostType` (`smart`, the only type in Off-peak), `config`,
    `G_PeriodTime` = `"time1=HH:MM-HH:MM&time2=..."`, up to 5 slots. Slots must not overlap
    (both ends included, so `07:00-12:00` and `12:00-14:00` overlap) and a slot's start must
    differ from its end.
  - Switching from another mode, Boost starts off (`boost` `"0"`, `config` `""`) and PV Linkage
    starts with `boostType` `manual` and `importGrid` `"0"`. Staying in the same mode keeps the
    current values.
