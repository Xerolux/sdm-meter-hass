"""The SDM Meter integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_CONNECTION_TYPE, CONF_SLAVE, CONN_RTU_OVER_TCP, DOMAIN
from .hub import SdmMeterHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SDM Meter from a config entry."""
    connection_type = entry.data.get(CONF_CONNECTION_TYPE, CONN_RTU_OVER_TCP)
    hub = SdmMeterHub(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_SLAVE],
        connection_type,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        await hub.close()
        _LOGGER.exception("Failed to set up SDM Meter entry %s", entry.entry_id)
        return False

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.close()

    return unload_ok
