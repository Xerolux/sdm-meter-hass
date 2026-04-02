from __future__ import annotations

from custom_components.sdm_meter.const import MODEL_SDM120, MODEL_SDM630
from custom_components.sdm_meter.register_map import (
    build_register_chunks,
    is_sensor_supported_for_model,
)


def test_model_filter_for_single_phase_meter() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM120, "l1_power")
    assert is_sensor_supported_for_model(MODEL_SDM120, "import_kwh")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "l2_current")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "total_system_power")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "l1_import_kwh")


def test_model_filter_for_three_phase_meter() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM630, "l2_current")


def test_build_register_chunks_groups_addresses() -> None:
    addresses = [0, 2, 4, 100, 102, 200]
    chunks = build_register_chunks(addresses)
    assert chunks == [(0, 6), (100, 4), (200, 2)]


def test_build_register_chunks_empty() -> None:
    assert build_register_chunks([]) == []
