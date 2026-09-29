"""Constants for the Growatt THOR integration."""

from datetime import timedelta

DOMAIN = "growatt_thor_cloud"

# Config entry key: we store Growatt's password hash, never the plain password.
CONF_PASSWORD_HASH = "password_hash"

DEFAULT_BASE_URL = "https://evcharge.growatt.com"
# The charger backend identifies ShinePhone users as "SHINE" + account name.
DEFAULT_USER_PREFIX = "SHINE"

# Matches the charger's meter upload period (G_MeterValueInterval = 60 s).
SCAN_INTERVAL = timedelta(seconds=60)

# Only single-connector home chargers are supported for now.
CONNECTOR_ID = 1

# OCPP connector states for which a transaction is running.
ACTIVE_STATES = ("Charging", "SuspendedEV", "SuspendedEVSE")
