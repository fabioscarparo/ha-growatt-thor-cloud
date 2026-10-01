"""Tests for the Growatt THOR API client."""

from __future__ import annotations

from datetime import datetime

import pytest

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.growatt_thor_cloud.api import (
    GrowattThorApi,
    GrowattThorApiError,
    GrowattThorAuthError,
    hash_password,
)
from custom_components.growatt_thor_cloud.const import DEFAULT_BASE_URL

LOGIN_URL = f"{DEFAULT_BASE_URL}/ocpp/user"
CONFIG_URL = f"{DEFAULT_BASE_URL}/ocpp/api/configInfo"
CMD_URL = f"{DEFAULT_BASE_URL}/ocpp/cmd/"


def test_hash_password() -> None:
    """Single-digit bytes are padded with "c" instead of "0"."""
    # MD5("test") = 098f6bcd...: the leading 0x09 byte becomes "c9".
    assert hash_password("test") == "c98f6bcd4621d373cade4e832627b4f6"


async def test_relogin_on_expired_token(hass, aioclient_mock) -> None:
    """Lazy login, token header, secret stripping and a single retry on 501."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "data": "Success", "token": "t1"})
    aioclient_mock.post(
        CONFIG_URL, json={"code": 0, "data": {"G_MaxCurrent": 16, "G_WifiPassword": "x"}}
    )
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")

    config = await api.async_get_config("SN1")

    assert config == {"G_MaxCurrent": 16}  # secrets are dropped
    login_call = aioclient_mock.mock_calls[0]
    assert login_call[2]["userId"] == "SHINEuser"
    assert login_call[2]["password"] == "hash"
    assert aioclient_mock.mock_calls[1][3]["Authorization"] == "t1"

    aioclient_mock.clear_requests()
    aioclient_mock.post(CONFIG_URL, json={"code": 501, "data": "User not logged in"})
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t2"})
    with pytest.raises(GrowattThorApiError):
        # Still 501 after re-login -> surfaced as an API error.
        await api.async_get_config("SN1")
    assert [call[1].path for call in aioclient_mock.mock_calls] == [
        "/ocpp/api/configInfo",
        "/ocpp/user",
        "/ocpp/api/configInfo",
    ]


async def test_login_rejected(hass, aioclient_mock) -> None:
    """A non-zero login code is an auth error, not a transport error."""
    aioclient_mock.post(LOGIN_URL, json={"code": 1, "data": "Password error"})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "bad")
    with pytest.raises(GrowattThorAuthError):
        await api.login()


async def test_set_charge_mode_payload(hass, aioclient_mock) -> None:
    """Mode updates go to /ocpp/chargeMode with cmd=update and a string connector id."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(f"{DEFAULT_BASE_URL}/ocpp/chargeMode", json={"code": 0})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")

    await api.async_set_charge_mode("SN1", 1, {"mode": "fast"})

    assert aioclient_mock.mock_calls[1][2] == {
        "userId": "SHINEuser",
        "lan": 1,
        "cmd": "update",
        "chargeId": "SN1",
        "connectorId": "1",
        "mode": "fast",
    }


async def test_reservations_payload(hass, aioclient_mock) -> None:
    """The reservation list is read from /ocpp/api/ReserveNow."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(
        f"{DEFAULT_BASE_URL}/ocpp/api/ReserveNow",
        json={"code": 0, "data": [{"reservationId": 7}]},
    )
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")

    assert await api.async_get_reservations("SN1", 1) == [{"reservationId": 7}]
    assert aioclient_mock.mock_calls[1][2] == {
        "userId": "SHINEuser",
        "lan": 1,
        "chargeId": "SN1",
        "connectorId": "1",
    }


async def test_login_paused_after_failure(hass, aioclient_mock) -> None:
    """A failed login blocks further attempts for a while instead of hammering the server."""
    aioclient_mock.post(LOGIN_URL, exc=TimeoutError())
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")
    with pytest.raises(GrowattThorApiError):
        await api.login()
    with pytest.raises(GrowattThorApiError, match="paused"):
        await api.login()
    assert aioclient_mock.call_count == 1


async def test_rate_limited(hass, aioclient_mock) -> None:
    """HTTP 429 is a temporary API error, not an auth problem."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(f"{DEFAULT_BASE_URL}/ocpp/api/list", status=429)
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")
    with pytest.raises(GrowattThorApiError, match="429"):
        await api.async_get_chargers()


async def test_schedule_payloads(hass, aioclient_mock) -> None:
    """Limited start, reservation and cancel are sent in the expected wire format."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(f"{DEFAULT_BASE_URL}/ocpp/cmd/", json={"code": 0})
    aioclient_mock.post(f"{DEFAULT_BASE_URL}/ocpp/api/updateReserve", json={"code": 0})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")
    base = {"userId": "SHINEuser", "lan": 1}

    await api.async_start_charging("SN1", 1, "G_SetTime", "90")
    assert aioclient_mock.mock_calls[-1][2] == {
        **base,
        "action": "remoteStartTransaction",
        "chargeId": "SN1",
        "connectorId": "1",
        "cKey": "G_SetTime",
        "cValue": "90",
        "loopType": -1,
        "loopValue": "1:30",
    }

    await api.async_reserve_charging(
        "SN1", 1, datetime(2026, 9, 29, 23, 5), every_day=False, limit_key="G_SetEnergy", limit_value="20"
    )
    assert aioclient_mock.mock_calls[-1][2] == {
        **base,
        "action": "ReserveNow",
        "expiryDate": "2026-09-29T23:05:00.000Z",
        "connectorId": "1",
        "chargeId": "SN1",
        "loopType": -1,
        "loopValue": "23:05",
        "cKey": "G_SetEnergy",
        "cValue": "20",
    }

    reservation = {
        "reservationId": 7,
        "connectorId": 1,
        "expiryDate": "2026-09-29T23:05:00.000Z",
        "loopType": 0,
        "loopValue": "23:05",
        "cKey": "",
        "cValue": 0,
        "chargeId": "SN1",
    }
    await api.async_cancel_reservation("SN1", reservation)
    sent = aioclient_mock.mock_calls[-1][2]
    assert (sent["ctype"], sent["sn"], sent["reservationId"]) == ("2", "SN1", 7)


async def test_command_result_in_type(hass, aioclient_mock) -> None:
    """Commands report their result in "type", with or without "code"."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(CMD_URL, json={"type": 0, "data": "Command sent"})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")
    await api.async_start_charging("SN1", 1)  # No "code": still a success.

    aioclient_mock.clear_requests()
    aioclient_mock.post(CMD_URL, json={"code": 0, "type": 1, "data": "Rejected"})
    with pytest.raises(GrowattThorApiError, match="Rejected"):
        await api.async_stop_charging("SN1", 1, "5")

    aioclient_mock.clear_requests()
    aioclient_mock.post(CMD_URL, json={"type": 501, "data": "Not logged in"})
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t2"})
    with pytest.raises(GrowattThorApiError):
        await api.async_start_charging("SN1", 1)
    assert [call[1].path for call in aioclient_mock.mock_calls] == [
        "/ocpp/cmd/",
        "/ocpp/user",
        "/ocpp/cmd/",
    ]


async def test_type_ignored_outside_commands(hass, aioclient_mock) -> None:
    """Other endpoints answer with "code"; a "type" field there means nothing."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(CONFIG_URL, json={"code": 0, "type": 1, "data": {"G_MaxCurrent": 16}})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")
    assert await api.async_get_config("SN1") == {"G_MaxCurrent": 16}


async def test_unlock_payload(hass, aioclient_mock) -> None:
    """Unlock is a /ocpp/api/ command with a string connector id."""
    aioclient_mock.post(LOGIN_URL, json={"code": 0, "token": "t"})
    aioclient_mock.post(f"{DEFAULT_BASE_URL}/ocpp/api/", json={"code": 0, "data": "ok"})
    api = GrowattThorApi(async_get_clientsession(hass), "user", "hash")

    await api.async_unlock("SN1", 1)
    assert aioclient_mock.mock_calls[-1][2] == {
        "userId": "SHINEuser",
        "lan": 1,
        "cmd": "unlock",
        "chargeId": "SN1",
        "connectorId": "1",
    }
