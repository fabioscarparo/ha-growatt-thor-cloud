"""Tests for the Growatt THOR API client."""

from __future__ import annotations

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
