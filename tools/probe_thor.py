#!/usr/bin/env python3
"""Read-only probe for the Growatt EV charger cloud API.

Usage:
    python3 tools/probe_thor.py            # prompts for Growatt username/password
    GROWATT_USER=... python3 tools/probe_thor.py

Only calls read endpoints (login, list, configInfo, charge/info, ReserveNow, chargeMode,
the installer-protected settings, the time-slot power limits, the last sessions and the
time zone list) and prints the responses as JSON, to map fields to Home Assistant
entities. Credentials are redacted, and personal data (account name, serial numbers,
network details, site) is masked, so the output can be attached to a public issue.
Standard library only, so it runs anywhere without installing Home Assistant.
"""

import getpass
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("GROWATT_CHARGE_HOST", "https://evcharge.growatt.com")
# The charger backend identifies a Growatt account as "SHINE" + account name.
PREFIX = os.environ.get("GROWATT_CHARGE_PREFIX", "SHINE")
LAN = 1  # Response language: 1 = English.
USER_AGENT = "MyApp/8.5.6.0 ShinePhone Dalvik/2.1.0 (Linux; U; Android 14)"

# Keys whose values must never be printed: the token, credentials stored on the
# charger and the installer password of the protected settings.
SECRET_KEYS = {
    "token",
    "G_WifiPassword",
    "G_CardPin",
    "G_Authentication",
    "G_4GPassword",
    "G_4GUserName",
    "configWord",
    "password",
}
# Personal data, masked too so the output can be attached to a public issue.
PRIVATE_KEYS = {
    "userId",
    "mac",
    "ip",
    "gateway",
    "dns",
    "G_WifiSSID",
    "address",
    "site",
    "siteId",
    "orderId",
    "SerialNumber",
    "installer",
}
# Values masked wherever they appear, titles included: the account name and the
# serial numbers (filled in once known).
MASKS: dict[str, str] = {}
LAST_SESSIONS = 3  # Charge records to show.
TIME_ZONES = 5  # Entries of the time zone list to show, enough to see the format.


def growatt_hash(password: str) -> str:
    """MD5 hex digest where single-digit bytes are padded with 'c' instead of '0'."""
    out = []
    for b in hashlib.md5(password.encode()).digest():
        h = format(b, "x")
        out.append("c" + h if len(h) == 1 else h)
    return "".join(out)


def post(path: str, payload: dict, token: str = "") -> dict:
    """POST JSON; non-JSON replies come back as {"_raw": body} and HTTP or network
    failures as {"_error": reason}, so one failing endpoint does not stop the probe."""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    if token:
        req.add_header("Authorization", token)  # Raw token, no "Bearer" prefix.
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
    except (urllib.error.URLError, TimeoutError) as err:
        return {"_error": str(err)}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body}


def redact(data):
    """Recursively mask SECRET_KEYS and PRIVATE_KEYS; empty values stay visible to show
    they are unset."""
    if isinstance(data, dict):
        return {
            k: "<redacted>" if k in SECRET_KEYS and v
            else "<private>" if k in PRIVATE_KEYS and v
            else redact(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data


def mask(text: str) -> str:
    """Replace the account name and serial numbers wherever they appear."""
    for value, placeholder in MASKS.items():
        text = text.replace(value, placeholder)
    return text


def dump(title: str, data: dict) -> None:
    print(mask(f"\n===== {title} ====="))
    print(mask(json.dumps(redact(data), indent=2, ensure_ascii=False)))


def main() -> int:
    """Log in, then dump every read endpoint for each charger and connector."""
    account = os.environ.get("GROWATT_USER") or input("Growatt username: ")
    password = os.environ.get("GROWATT_PASSWORD") or getpass.getpass("Growatt password: ")
    user_id = PREFIX + account
    if len(account) >= 4:  # Shorter names would mask unrelated text.
        MASKS[account] = "<account>"

    login = post("/ocpp/user", {
        "cmd": "shineLogin",
        "userId": user_id,
        "password": growatt_hash(password),
        "lan": LAN,
    })
    token = login.get("token", "")
    dump("login", login)
    if not token:
        print("\nLogin did not return a token; stopping.", file=sys.stderr)
        return 1

    chargers = post("/ocpp/api/list", {"userId": user_id, "lan": LAN}, token)
    for index, charger in enumerate(chargers.get("data") or [], 1):
        if charger.get("chargeId"):
            MASKS[str(charger["chargeId"])] = f"<serial {index}>"
    dump("list", chargers)
    # Settings that need the installer password (listed in "sfield").
    dump("noConfig", post("/ocpp/api/", {"cmd": "noConfig", "userId": user_id, "lan": LAN}, token))
    zones = post("/ocpp/api/timeZoneList2", {}, token)
    if isinstance(zones.get("data"), list):
        zones["data"] = zones["data"][:TIME_ZONES]
    dump(f"timeZoneList2 (first {TIME_ZONES})", zones)

    for charger in chargers.get("data") or []:
        sn = charger.get("chargeId")
        dump(f"configInfo {sn}", post("/ocpp/api/configInfo",
                                      {"sn": sn, "userId": user_id, "lan": LAN}, token))
        dump(f"selectLimitPower {sn}", post("/ocpp/api/", {
            "cmd": "selectLimitPower", "chargeId": sn, "userId": user_id, "lan": LAN,
        }, token))
        dump(f"chargeRecord {sn} (last {LAST_SESSIONS})", post("/ocpp/api/chargeRecord", {
            "sn": sn, "page": 1, "psize": LAST_SESSIONS, "userId": user_id, "lan": LAN,
        }, token))
        # Connectors are numbered from 1, as in OCPP.
        for connector_id in range(1, int(charger.get("connectors") or 1) + 1):
            dump(f"charge/info {sn} connector {connector_id}", post("/ocpp/charge/info", {
                "sn": sn, "connectorId": connector_id, "userId": user_id, "lan": LAN,
            }, token))
            dump(f"ReserveNow {sn} connector {connector_id}", post("/ocpp/api/ReserveNow", {
                "chargeId": sn, "connectorId": str(connector_id), "userId": user_id, "lan": LAN,
            }, token))
            dump(f"chargeMode {sn} connector {connector_id}", post("/ocpp/chargeMode", {
                "cmd": "select", "chargeId": sn, "connectorId": connector_id, "userId": user_id,
            }, token))
    return 0


if __name__ == "__main__":
    sys.exit(main())
