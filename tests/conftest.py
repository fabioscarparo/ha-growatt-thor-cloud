"""Fixtures for the Growatt THOR tests."""

from __future__ import annotations

import copy
from unittest.mock import AsyncMock, patch

import pytest

SN = "SMS0000000000001"  # Fake serial, same format as real ones.

# Anonymised from a real THOR 07AS-P response.
CHARGERS = [
    {
        "chargeId": SN,
        "name": SN,
        "vendor": "Growatt",
        "model": "AC",
        "connectors": 1,
        "unit": "EUR",
        "symbol": "€",
        "status_1": "Available",
        "G_SolarMode": "2",
    }
]
CONFIG = {
    "chargeId": SN,
    "deviceModel": "THOR 07AS-P-V1",
    "version": "THOR_07ASB-VA1.2.3.0-NOVO",
    "mac": "00:11:22:33:44:55",
    "ip": "192.0.2.10",
    "unit": "EUR",
    "online": 0,
    "elockstate": "unlocked",
    "G_MaxCurrent": 32,
    "G_SolarMode": 2,
    "G_ChargerMode": "3",
    "G_ExternalLimitPowerEnable": 0,
    "G_LCDCloseEnable": "Disable",
    "G_FullContinueChargeEnable": "Disable",
    "G_SolarLimitPower": 1.38,
    "power": 7000,
    "G_ExternalSamplingCurWring": 1,
    "G_PowerMeterType": "Eastron SDM230",
    "G_PowerMeterAddr": 1,
    "priceConf": [{"price": "0.21", "time": "00:00-23:59"}],
    "UnlockConnectorOnEVSideDisconnect": "true",
    "sysTimeZone": "UTC+2",
    "G_DaylightSavingTime": "00-00&00-00",
    "G_NetType": "",
    "G_NetworkMode": "STATIC",
    "G_MaxTemperature": 80,
    "isSupportPL": True,
    "isSupportLoadBalancing": True,
    "isSupportLowRateMode": True,
    "isSupport_LCDEnable": True,
}
# Idle charger: settings and modes can be changed.
CONNECTOR = {
    "chargeId": SN,
    "connectorId": 1,
    "status": "Available",
    "current": 0,
    "voltage": 0,
    "energy": 0,
    "ctime": 0,
    "cost": 0,
    "rate": 0,  # Session rate: 0 in real responses even with a tariff set.
    "transactionId": 0,
    "online": 0,
    "elockstate": "unlocked",
    "errorCode": "NoError",
    "vendorErrorCode": "",
}
# Fields of a running session, applied over CONNECTOR.
CHARGING = {
    "status": "Charging",
    "current": 16,
    "voltage": 230,
    "energy": 3.5,
    "ctime": 42,
    "cost": 0.56,
    "transactionId": 1234,
    "online": 1,
    "elockstate": "locked",
}
CHARGE_MODE = {
    "chargeId": f"{SN}_1",
    "connectorId": 1,
    "mode": "pvLinkage",
    "boost": 0,
    "boostType": "manual",
    "config": "",
    "importGrid": 0.0,
    "G_PeriodTime": "",
    "G_ExternalSamplingCurWring": "0",
    "G_PowerMeterType": "",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """HA only loads custom_components when this fixture is active."""
    yield


@pytest.fixture
def mock_api():
    """Patch the API client where setup and the config flow build it.

    Deep copies keep one test's optimistic writes from leaking into the fixtures.
    """
    api = AsyncMock()
    api.async_get_chargers.return_value = copy.deepcopy(CHARGERS)
    api.async_get_config.side_effect = lambda sn: copy.deepcopy(CONFIG)
    api.async_get_connector.side_effect = lambda sn, cid: copy.deepcopy(CONNECTOR)
    api.async_get_reservations.side_effect = lambda sn, cid: []
    api.async_get_charge_mode.side_effect = lambda sn, cid: copy.deepcopy(CHARGE_MODE)
    api.async_get_sessions.side_effect = lambda sn, count: []
    with (
        patch("custom_components.growatt_thor_cloud.GrowattThorApi", return_value=api),
        patch("custom_components.growatt_thor_cloud.config_flow.GrowattThorApi", return_value=api),
    ):
        yield api
