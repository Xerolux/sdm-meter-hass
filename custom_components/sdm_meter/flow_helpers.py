"""Helpers for config and options flow validation."""

from __future__ import annotations

from collections.abc import Mapping

import voluptuous as vol

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_SLAVE,
    CONF_UPDATE_INTERVAL,
    CONN_RTU_OVER_TCP,
    CONN_TCP,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DEFAULT_UPDATE_INTERVAL,
    MODEL_SDM120,
    MODEL_SDM630,
)

MODELS = (MODEL_SDM630, MODEL_SDM120)
CONNECTION_TYPES = (CONN_RTU_OVER_TCP, CONN_TCP)


def build_config_schema(current: Mapping[str, object] | None = None) -> vol.Schema:
    """Build schema for config and options flow."""
    current = current or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=current.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_MODEL,
                default=current.get(CONF_MODEL, DEFAULT_MODEL),
            ): vol.In(MODELS),
            vol.Required(
                CONF_CONNECTION_TYPE,
                default=current.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE),
            ): vol.In(CONNECTION_TYPES),
            vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): vol.All(
                str,
                vol.Length(min=1),
            ),
            vol.Required(CONF_PORT, default=current.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                int,
                vol.Range(min=1, max=65535),
            ),
            vol.Required(CONF_SLAVE, default=current.get(CONF_SLAVE, DEFAULT_SLAVE)): vol.All(
                int,
                vol.Range(min=1, max=247),
            ),
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=current.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): vol.All(int, vol.Range(min=1, max=3600)),
        }
    )


def build_unique_id(host: str, port: int, slave: int) -> str:
    """Build stable unique-id for a Modbus endpoint."""
    return f"{host}:{port}:{slave}"
