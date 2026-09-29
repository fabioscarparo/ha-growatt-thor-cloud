"""Constants for the Growatt THOR integration."""

from datetime import timedelta

DOMAIN = "growatt_thor_cloud"

# Config entry key: we store Growatt's password hash, never the plain password.
CONF_PASSWORD_HASH = "password_hash"
# Options key: polling interval in seconds.
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_BASE_URL = "https://evcharge.growatt.com"
# The charger backend identifies app users as "SHINE" + account name.
DEFAULT_USER_PREFIX = "SHINE"

# Default matches the charger's meter upload period (G_MeterValueInterval = 60 s).
DEFAULT_SCAN_INTERVAL = 60  # s
MIN_SCAN_INTERVAL = 30  # s
MAX_SCAN_INTERVAL = 600  # s
# Settings change rarely: read them less often, and right after a write from HA.
CONFIG_REFRESH_INTERVAL = timedelta(minutes=5)
# On consecutive failures, poll at these intervals (s) instead, capped at the last.
BACKOFF_INTERVALS = (120, 300, 600)
# Keep showing the last data for this long before entities become unavailable.
STALE_DATA_GRACE = timedelta(minutes=5)

# Only single-connector home chargers are supported for now.
CONNECTOR_ID = 1

# OCPP connector states for which a transaction is running.
ACTIVE_STATES = ("Charging", "SuspendedEV", "SuspendedEVSE")

# Session limit keys (cKey): stop at a cost, an energy or a duration in minutes.
LIMIT_COST = "G_SetAmount"
LIMIT_ENERGY = "G_SetEnergy"
LIMIT_DURATION = "G_SetTime"
