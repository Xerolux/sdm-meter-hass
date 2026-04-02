"""Config flow for SDM Meter integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    DOMAIN, DEFAULT_NAME, DEFAULT_PORT, CONF_SLAVE, DEFAULT_SLAVE,
    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, CONF_NAME,
    CONF_MODEL, MODEL_SDM630, MODEL_SDM120, DEFAULT_MODEL,
    CONF_CONNECTION_TYPE, CONN_RTU_OVER_TCP, CONN_TCP, DEFAULT_CONNECTION_TYPE
)

_LOGGER = logging.getLogger(__name__)

MODELS = [MODEL_SDM630, MODEL_SDM120]
CONNECTION_TYPES = [CONN_RTU_OVER_TCP, CONN_TCP]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(MODELS),
        vol.Required(CONF_CONNECTION_TYPE, default=DEFAULT_CONNECTION_TYPE): vol.In(CONNECTION_TYPES),
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
        vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
    }
)

class SdmMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SDM Meter."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # You could add validation here to check if the modbus server is reachable
            # For now, we just create the entry
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} ({user_input[CONF_HOST]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SdmMeterOptionsFlowHandler(config_entry)


class SdmMeterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SDM Meter."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with the new options (we store them in options)
            # Alternatively, since we use `entry.data` in __init__ and sensor.py,
            # we should update the entry data directly.
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        current_config = self.config_entry.data

        options_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=current_config.get(CONF_NAME, DEFAULT_NAME)): str,
                vol.Required(CONF_MODEL, default=current_config.get(CONF_MODEL, DEFAULT_MODEL)): vol.In(MODELS),
                vol.Required(CONF_CONNECTION_TYPE, default=current_config.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE)): vol.In(CONNECTION_TYPES),
                vol.Required(CONF_HOST, default=current_config.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=current_config.get(CONF_PORT, DEFAULT_PORT)): int,
                vol.Required(CONF_SLAVE, default=current_config.get(CONF_SLAVE, DEFAULT_SLAVE)): int,
                vol.Required(CONF_UPDATE_INTERVAL, default=current_config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
