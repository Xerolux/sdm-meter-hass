"""Constants for the SDM Meter integration."""
from datetime import timedelta

DOMAIN = "sdm_meter"
DEFAULT_NAME = "SDM Meter"
DEFAULT_PORT = 502
DEFAULT_UPDATE_INTERVAL = 5  # seconds
DEFAULT_SLAVE = 11

CONF_NAME = "name"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE = "slave"
CONF_UPDATE_INTERVAL = "update_interval"

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
