"""Async client for the Growatt EV charger cloud API (evcharge.growatt.com/ocpp).

Every call is a JSON POST carrying `userId` and `lan`; the server answers
`{"code": 0, "data": ...}` on success and `code: 501` once the token expires.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import hashlib
import json
import time
from typing import Any

import aiohttp

from .const import DEFAULT_BASE_URL, DEFAULT_USER_PREFIX, LIMIT_DURATION

LAN = 1  # Response language: 1 = English.
USER_AGENT = "MyApp/8.5.6.0 ShinePhone"
TIMEOUT = aiohttp.ClientTimeout(total=30)
CODE_OK = 0
CODE_NOT_LOGGED_IN = 501
# After a failed login, wait before trying again: repeated logins are what gets
# Growatt accounts rate limited or locked.
LOGIN_COOLDOWN = 300  # s

# Config fields that hold credentials; never keep them in memory or state.
SECRET_KEYS = frozenset(
    {"G_WifiPassword", "G_CardPin", "G_Authentication", "G_4GPassword", "G_4GUserName"}
)


class GrowattThorError(Exception):
    """Base error for the Growatt THOR API."""


class GrowattThorAuthError(GrowattThorError):
    """Login was rejected."""


class GrowattThorApiError(GrowattThorError):
    """The API could not be reached or returned an error; worth retrying later."""


def hash_password(password: str) -> str:
    """Return Growatt's MD5 variant: single-digit bytes are padded with 'c', not '0'."""
    out = []
    for byte in hashlib.md5(password.encode()).digest():
        hex_byte = format(byte, "x")
        out.append("c" + hex_byte if len(hex_byte) == 1 else hex_byte)
    return "".join(out)


class GrowattThorApi:
    """Session-token client; logs in lazily and again whenever the token expires."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password_hash: str,
        base_url: str = DEFAULT_BASE_URL,
        user_prefix: str = DEFAULT_USER_PREFIX,
    ) -> None:
        self._session = session
        self._user_id = user_prefix + username
        self._password_hash = password_hash
        self._base_url = base_url.rstrip("/")
        self._token: str | None = None
        # One login at a time: concurrent calls that all see an expired token
        # must not each log in.
        self._login_lock = asyncio.Lock()
        self._login_retry_at = 0.0  # time.monotonic() before which login is paused

    async def login(self) -> None:
        """Get a fresh token; raises GrowattThorAuthError if credentials are rejected."""
        async with self._login_lock:
            await self._login()

    # --- Read -------------------------------------------------------------

    async def async_get_chargers(self) -> list[dict[str, Any]]:
        """Chargers bound to the account, with a summary of their settings."""
        return (await self._call("/ocpp/api/list", {})).get("data") or []

    async def async_get_config(self, sn: str) -> dict[str, Any]:
        """Full charger settings, minus credential fields."""
        data = (await self._call("/ocpp/api/configInfo", {"sn": sn})).get("data") or {}
        return {k: v for k, v in data.items() if k not in SECRET_KEYS}

    async def async_get_connector(self, sn: str, connector_id: int) -> dict[str, Any]:
        """Live connector data and its reservations.

        Returns {"data": {status, V/A, session energy, cost, transactionId...},
        "reservations": [ReserveNow entries]}.
        """
        payload = {"sn": sn, "connectorId": connector_id}
        resp = await self._call("/ocpp/charge/info", payload)
        return {"data": resp.get("data") or {}, "reservations": resp.get("ReserveNow") or []}

    async def async_get_charge_mode(self, sn: str, connector_id: int) -> dict[str, Any]:
        """Active charge mode (fast / offPeak / pvLinkage) and its parameters."""
        payload = {"cmd": "select", "chargeId": sn, "connectorId": connector_id}
        return (await self._call("/ocpp/chargeMode", payload)).get("data") or {}

    # --- Write ------------------------------------------------------------

    async def async_set_config(self, sn: str, key: str, value: Any) -> None:
        """Change one setting; `value` must already be in the wire format for `key`."""
        await self._call("/ocpp/api/config", {"chargeId": sn, key: value})

    async def async_set_charge_mode(
        self, sn: str, connector_id: int, fields: dict[str, Any]
    ) -> None:
        """Switch charge mode; `fields` is the whole mode object (mode, boost, importGrid...)."""
        await self._call(
            "/ocpp/chargeMode",
            {"cmd": "update", "chargeId": sn, "connectorId": str(connector_id), **fields},
        )

    async def async_start_charging(
        self,
        sn: str,
        connector_id: int,
        limit_key: str | None = None,
        limit_value: str | None = None,
    ) -> None:
        """Send an OCPP RemoteStartTransaction, optionally stopping at a limit.

        `limit_key` is G_SetAmount (cost), G_SetEnergy (kWh) or G_SetTime (minutes).
        """
        payload: dict[str, Any] = {
            "action": "remoteStartTransaction",
            "chargeId": sn,
            "connectorId": str(connector_id),
        }
        if limit_key:
            payload |= {"cKey": limit_key, "cValue": limit_value}
            if limit_key == LIMIT_DURATION:
                # A duration start also carries it as "h:m" (not zero-padded).
                minutes = int(float(limit_value or 0))
                payload |= {"loopType": -1, "loopValue": f"{minutes // 60}:{minutes % 60}"}
        await self._call("/ocpp/cmd/", payload)

    async def async_reserve_charging(
        self,
        sn: str,
        connector_id: int,
        start: datetime,
        every_day: bool,
        limit_key: str | None = None,
        limit_value: str | None = None,
    ) -> None:
        """Schedule a start at `start` (charger local time), once or every day."""
        payload: dict[str, Any] = {
            "action": "ReserveNow",
            # Local wall-clock time with a literal "Z": that is the format the
            # server expects, not UTC.
            "expiryDate": start.strftime("%Y-%m-%dT%H:%M:00.000Z"),
            "connectorId": str(connector_id),
            "chargeId": sn,
            "loopType": 0 if every_day else -1,
            "loopValue": start.strftime("%H:%M"),
        }
        if limit_key:
            payload |= {"cKey": limit_key, "cValue": limit_value}
        await self._call("/ocpp/cmd/", payload)

    async def async_cancel_reservation(self, sn: str, reservation: dict[str, Any]) -> None:
        """Delete a reservation, echoing it back as returned by charge/info."""
        fields = {
            key: reservation.get(key)
            for key in (
                "cKey",
                "cValue",
                "connectorId",
                "expiryDate",
                "loopValue",
                "loopType",
                "reservationId",
            )
        }
        await self._call("/ocpp/api/updateReserve", {**fields, "sn": sn, "ctype": "2"})

    async def async_stop_charging(
        self, sn: str, connector_id: int, transaction_id: str
    ) -> None:
        """Send an OCPP RemoteStopTransaction for the running transaction."""
        await self._call(
            "/ocpp/cmd/",
            {
                "action": "remoteStopTransaction",
                "chargeId": sn,
                "connectorId": str(connector_id),
                "transactionId": transaction_id,
            },
        )

    # --- Transport --------------------------------------------------------

    async def _login(self) -> None:
        """Log in; the caller holds the login lock. Failures pause further logins."""
        wait = self._login_retry_at - time.monotonic()
        if wait > 0:
            raise GrowattThorApiError(f"Login paused after a failure, retry in {wait:.0f} s")
        try:
            data = await self._request(
                "/ocpp/user",
                {
                    "cmd": "shineLogin",
                    "userId": self._user_id,
                    "password": self._password_hash,
                    "lan": LAN,
                },
            )
        except GrowattThorApiError:
            self._login_retry_at = time.monotonic() + LOGIN_COOLDOWN
            raise
        token = data.get("token")
        if data.get("code") != CODE_OK or not token:
            self._login_retry_at = time.monotonic() + LOGIN_COOLDOWN
            raise GrowattThorAuthError(str(data.get("data") or "Login failed"))
        self._login_retry_at = 0.0
        self._token = token

    async def _refresh_token(self, stale: str | None) -> None:
        """Log in unless a concurrent call already replaced the `stale` token."""
        async with self._login_lock:
            if self._token is None or self._token == stale:
                await self._login()

    async def _call(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Authenticated call; logs in again once if the token has expired."""
        payload = {"userId": self._user_id, "lan": LAN, **payload}
        if self._token is None:
            await self._refresh_token(None)
        used_token = self._token
        data = await self._request(path, payload)
        if data.get("code") == CODE_NOT_LOGGED_IN:
            await self._refresh_token(used_token)
            data = await self._request(path, payload)
        if data.get("code") != CODE_OK:
            raise GrowattThorApiError(f"{path} failed: {data.get('data')}")
        return data

    async def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON and decode the reply; any transport or format problem is an API error."""
        headers = {"User-Agent": USER_AGENT}
        if self._token:
            headers["Authorization"] = self._token  # Raw token, no "Bearer" prefix.
        try:
            async with self._session.post(
                self._base_url + path, json=payload, headers=headers, timeout=TIMEOUT
            ) as resp:
                if resp.status == 429:
                    raise GrowattThorApiError(f"{path}: rate limited by Growatt (HTTP 429)")
                resp.raise_for_status()
                body = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GrowattThorApiError(f"{path} request failed: {err}") from err
        try:
            data = json.loads(body)
        except ValueError as err:
            raise GrowattThorApiError(f"{path} returned a non-JSON response") from err
        if not isinstance(data, dict):
            raise GrowattThorApiError(f"{path} returned an unexpected response")
        return data
