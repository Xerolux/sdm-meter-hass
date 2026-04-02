from __future__ import annotations

import pytest
import voluptuous as vol

from custom_components.sdm_meter.flow_helpers import build_config_schema, build_unique_id


def test_build_unique_id() -> None:
    assert build_unique_id("192.168.1.10", 502, 11) == "192.168.1.10:502:11"


def test_schema_accepts_valid_input() -> None:
    schema = build_config_schema()
    data = schema(
        {
            "name": "SDM Main",
            "model": "SDM630 (3-Phase)",
            "connection_type": "Modbus RTU-over-TCP",
            "host": "192.168.1.50",
            "port": 502,
            "slave": 11,
            "update_interval": 10,
        }
    )
    assert data["host"] == "192.168.1.50"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("port", 70000),
        ("slave", 0),
        ("update_interval", 0),
        ("host", ""),
    ],
)
def test_schema_rejects_invalid_ranges(field: str, value) -> None:
    schema = build_config_schema()
    payload = {
        "name": "SDM Main",
        "model": "SDM630 (3-Phase)",
        "connection_type": "Modbus RTU-over-TCP",
        "host": "192.168.1.50",
        "port": 502,
        "slave": 11,
        "update_interval": 10,
    }
    payload[field] = value

    with pytest.raises(vol.Invalid):
        schema(payload)
