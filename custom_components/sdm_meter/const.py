"""Constants for the SDM Meter integration."""
from datetime import timedelta

DOMAIN = "sdm_meter"
DEFAULT_NAME = "SDM Meter"
DEFAULT_PORT = 502
DEFAULT_UPDATE_INTERVAL = 5  # seconds
DEFAULT_SLAVE = 11

CONF_NAME = "name"
CONF_MODEL = "model"
CONF_CONNECTION_TYPE = "connection_type"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE = "slave"
CONF_UPDATE_INTERVAL = "update_interval"

MODEL_SDM630 = "SDM630 (3-Phase)"
MODEL_SDM120 = "SDM120/230 (1-Phase)"
DEFAULT_MODEL = MODEL_SDM630

CONN_RTU_OVER_TCP = "Modbus RTU-over-TCP"
CONN_TCP = "Modbus TCP"
DEFAULT_CONNECTION_TYPE = CONN_RTU_OVER_TCP

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
