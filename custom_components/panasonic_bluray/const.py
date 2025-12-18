"""Constants for the Panasonic Blu-ray integration."""
from datetime import timedelta

__version__ = "2.0.0"
PROJECT_URL = "https://github.com/albaintor/panasonic_bluray_remote"
ISSUE_URL = "{}issues".format(PROJECT_URL)

DOMAIN = "panasonic_bluray"
PANASONIC_COORDINATOR = "panasonic_coordinator"
PANASONIC_API = "panasonic_api"

NAME = "Panasonic Blu-ray"
DEFAULT_DEVICE_NAME = "Panasonic Blu-ray"
MANUFACTURER = "Panasonic"

STARTUP = """
-------------------------------------------------------------------
{}
Version: {}
This is a custom integration.
If you have any issues with this you need to open an issue here:
{}
-------------------------------------------------------------------
""".format(
    NAME, __version__, ISSUE_URL
)

# Polling intervals
DEFAULT_SCAN_INTERVAL = 5  # seconds
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60
CONF_SCAN_INTERVAL = "scan_interval"

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
MIN_TIME_BETWEEN_SCANS = SCAN_INTERVAL
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)

# API timeout
API_TIMEOUT = 5

# Attribute names for status
ATTR_DEVICE_MODE = "device_mode"
ATTR_PLAYBACK_STATE = "playback_state"
ATTR_SPEED_MULTIPLIER = "speed_multiplier"
ATTR_CLOCK_TIME = "clock_time"
ATTR_TRAY_OPEN = "tray_open"
