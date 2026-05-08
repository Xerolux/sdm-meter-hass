from __future__ import annotations

from custom_components.sdm_meter.const import (
    MODEL_SDM120,
    MODEL_SDM630,
    MODEL_SDM630_MID,
    MODEL_SDM72,
)
from custom_components.sdm_meter.register_map import (
    build_register_chunks,
    get_supported_addresses,
    is_sensor_supported_for_model,
)


def test_model_filter_for_single_phase_meter() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM120, "l1_power")
    assert is_sensor_supported_for_model(MODEL_SDM120, "import_kwh")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "l2_current")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "total_system_power")
    assert not is_sensor_supported_for_model(MODEL_SDM120, "l1_import_kwh")


def test_model_filter_for_three_phase_sdm630() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM630, "l2_current")
    assert is_sensor_supported_for_model(MODEL_SDM630, "total_system_power")
    assert is_sensor_supported_for_model(MODEL_SDM630, "total_import_power_demand")


def test_model_filter_for_three_phase_sdm630_mid() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "l2_current")
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "total_system_power")
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "total_import_power_demand")
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "total_export_power_demand")
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "max_total_import_power_demand")
    assert is_sensor_supported_for_model(MODEL_SDM630_MID, "max_total_export_power_demand")


def test_model_filter_for_three_phase_sdm72() -> None:
    assert is_sensor_supported_for_model(MODEL_SDM72, "l2_current")
    assert is_sensor_supported_for_model(MODEL_SDM72, "total_system_power")


def test_three_phase_models_expose_all_registers() -> None:
    from custom_components.sdm_meter.register_map import SENSOR_ADDRESSES

    for model in (MODEL_SDM630, MODEL_SDM630_MID, MODEL_SDM72):
        supported = get_supported_addresses(model)
        assert len(supported) == len(SENSOR_ADDRESSES), (
            f"Model {model} should support all registers"
        )


def test_single_phase_model_exposes_subset() -> None:
    from custom_components.sdm_meter.register_map import SENSOR_ADDRESSES

    supported = get_supported_addresses(MODEL_SDM120)
    assert len(supported) < len(SENSOR_ADDRESSES)


def test_model_filter_with_none_returns_all() -> None:
    assert is_sensor_supported_for_model(None, "l2_current")
    assert is_sensor_supported_for_model(None, "anything_else")


def test_build_register_chunks_groups_addresses() -> None:
    addresses = [0, 2, 4, 100, 102, 200]
    chunks = build_register_chunks(addresses)
    assert chunks == [(0, 6), (100, 4), (200, 2)]


def test_build_register_chunks_empty() -> None:
    assert build_register_chunks([]) == []
