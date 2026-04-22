"""Config flow for SDM Meter integration."""

from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback

from .const import CONF_CONNECTION_TYPE, CONF_NAME, CONF_SLAVE, DOMAIN
from .flow_helpers import build_config_schema, build_unique_id
from .hub import SdmMeterHub

_LOGGER = logging.getLogger(__name__)


# pylint: disable=broad-except
async def _async_can_connect(user_input: dict, hass: HomeAssistant) -> bool:
    """Check if the target Modbus endpoint can be reached."""
    hub = SdmMeterHub(
        hass,
        user_input[CONF_HOST],
        user_input[CONF_PORT],
        user_input[CONF_SLAVE],
        user_input[CONF_CONNECTION_TYPE],
    )

    try:
        await hub.connect()
        return hub.connected
    except Exception:
        _LOGGER.exception(
            "Connection test failed for %s:%s",
            user_input[CONF_HOST],
            user_input[CONF_PORT],
        )
        return False
    finally:
        await hub.close()


class SdmMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for SDM Meter."""
    # pylint: disable=abstract-method

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = build_unique_id(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_SLAVE],
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            if await _async_can_connect(user_input, self.hass):
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} ({user_input[CONF_HOST]})",
                    data=user_input,
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=build_config_schema(user_input),
            errors=errors,
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

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=build_config_schema(dict(self.config_entry.data)),
        )
