"""Diagnostics support for SDM Meter."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    hub = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    diagnostics = {
        "entry": entry.as_dict(),
        "hub": {
            "connected": bool(hub and hub.connected),
        },
    }

    return async_redact_data(diagnostics, TO_REDACT)
