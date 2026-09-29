#!/usr/bin/env python3
"""Read-only probe for the Growatt EV charger cloud API.

Usage:
    python3 tools/probe_thor.py            # prompts for Growatt username/password
    GROWATT_USER=... python3 tools/probe_thor.py

Only calls read endpoints (login, list, configInfo, charge/info, ReserveNow, chargeMode)
and prints the responses as JSON, with credentials redacted, to map fields to Home
Assistant entities.
Standard library only, so it runs anywhere without installing Home Assistant.
"""

import getpass
import hashlib
import json
import os
import sys
import urllib.request

BASE_URL = os.environ.get("GROWATT_CHARGE_HOST", "https://evcharge.growatt.com")
# The charger backend identifies a Growatt account as "SHINE" + account name.
PREFIX = os.environ.get("GROWATT_CHARGE_PREFIX", "SHINE")
LAN = 1  # Response language: 1 = English.
USER_AGENT = "MyApp/8.5.6.0 ShinePhone Dalvik/2.1.0 (Linux; U; Android 14)"

# Keys whose values must never be printed (token plus credentials stored on the charger).
SECRET_KEYS = {
    "token",
    "G_WifiPassword",
    "G_CardPin",
    "G_Authentication",
    "G_4GPassword",
    "G_4GUserName",
}


def growatt_hash(password: str) -> str:
    """MD5 hex digest where single-digit bytes are padded with 'c' instead of '0'."""
    out = []
    for b in hashlib.md5(password.encode()).digest():
        h = format(b, "x")
        out.append("c" + h if len(h) == 1 else h)
    return "".join(out)


def post(path: str, payload: dict, token: str = "") -> dict:
    """POST JSON; non-JSON replies come back as {"_raw": body} so nothing is lost."""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    if token:
        req.add_header("Authorization", token)  # Raw token, no "Bearer" prefix.
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body}


def redact(data):
    """Recursively mask SECRET_KEYS; empty values stay visible to show they are unset."""
    if isinstance(data, dict):
        return {k: "<redacted>" if k in SECRET_KEYS and v else redact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data


def dump(title: str, data: dict) -> None:
    print(f"\n===== {title} =====")
    print(json.dumps(redact(data), indent=2, ensure_ascii=False))


def main() -> int:
    """Log in, then dump every read endpoint for each charger and connector."""
    account = os.environ.get("GROWATT_USER") or input("Growatt username: ")
    password = os.environ.get("GROWATT_PASSWORD") or getpass.getpass("Growatt password: ")
    user_id = PREFIX + account

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
    dump("list", chargers)

    for charger in chargers.get("data") or []:
        sn = charger.get("chargeId")
        dump(f"configInfo {sn}", post("/ocpp/api/configInfo",
                                      {"sn": sn, "userId": user_id, "lan": LAN}, token))
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
