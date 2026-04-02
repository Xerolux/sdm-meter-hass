"""Register map and selection helpers for SDM meters."""

from __future__ import annotations

from .const import MODEL_SDM120


def is_sensor_supported_for_model(model_name: str | None, key: str) -> bool:
    """Check if a sensor key is supported by the selected model."""
    if model_name == MODEL_SDM120:
        if "l2" in key or "l3" in key or "line" in key:
            return False
        if "total_system" in key or "sum_" in key or "avg_" in key or "average_" in key:
            return False
        if key.startswith("l1_") and key not in {"l1_neutral_volts", "l1_current", "l1_power"}:
            if "kwh" in key or "kvarh" in key or "thd" in key or "demand" in key:
                return False
    return True


def get_supported_addresses(model_name: str | None) -> dict[str, int]:
    """Return the filtered register map for the selected model."""
    return {
        key: address
        for key, address in SENSOR_ADDRESSES.items()
        if is_sensor_supported_for_model(model_name, key)
    }


def build_register_chunks(
    addresses: list[int],
    *,
    max_span: int = 100,
    register_width: int = 2,
) -> list[tuple[int, int]]:
    """Build contiguous-ish register chunks for batched Modbus reads."""
    if not addresses:
        return []

    chunks: list[tuple[int, int]] = []
    current_start = addresses[0]
    current_end = current_start + register_width

    for address in addresses[1:]:
        if address + register_width - current_start <= max_span:
            current_end = max(current_end, address + register_width)
        else:
            chunks.append((current_start, current_end - current_start))
            current_start = address
            current_end = address + register_width

    chunks.append((current_start, current_end - current_start))
    return chunks


SENSOR_ADDRESSES = {
    "l1_neutral_volts": 0,
    "l2_neutral_volts": 2,
    "l3_neutral_volts": 4,
    "l1_current": 6,
    "l2_current": 8,
    "l3_current": 10,
    "l1_power": 12,
    "l2_power": 14,
    "l3_power": 16,
    "l1_volt_amps": 18,
    "l2_volt_amps": 20,
    "l3_volt_amps": 22,
    "l1_volt_amps_reactive": 24,
    "l2_volt_amps_reactive": 26,
    "l3_volt_amps_reactive": 28,
    "l1_power_factor": 30,
    "l2_power_factor": 32,
    "l3_power_factor": 34,
    "l1_phase_angle": 36,
    "l2_phase_angle": 38,
    "l3_phase_angle": 40,
    "average_line_neutral_volt": 42,
    "average_line_current": 46,
    "sum_line_currents": 48,
    "total_system_power": 52,
    "total_system_volt_amps": 56,
    "total_system_var": 60,
    "total_system_power_factor": 62,
    "total_system_phase_angle": 66,
    "frequency": 70,
    "import_kwh": 72,
    "export_kwh": 74,
    "import_varh": 76,
    "export_varh": 78,
    "vah_total": 80,
    "ah_total": 82,
    "power_demand": 84,
    "max_power_demand": 86,
    "va_demand": 100,
    "max_va_demand": 102,
    "neutral_current_demand": 104,
    "max_neutral_current_demand": 106,
    "line1_line2_volts": 200,
    "line2_line3_volts": 202,
    "line3_line1_volts": 204,
    "avg_line_line_volts": 206,
    "neutral_current": 224,
    "l1_volts_thd": 234,
    "l2_volts_thd": 236,
    "l3_volts_thd": 238,
    "l1_current_thd": 240,
    "l2_current_thd": 242,
    "l3_current_thd": 244,
    "avg_volts_thd": 248,
    "avg_current_thd": 250,
    "l1_current_demand": 258,
    "l2_current_demand": 260,
    "l3_current_demand": 262,
    "max_l1_current_demand": 264,
    "max_l2_current_demand": 266,
    "max_l3_current_demand": 268,
    "l1l2_volts_thd": 334,
    "l2l3_volts_thd": 336,
    "l3l1_volts_thd": 338,
    "avg_line_line_volts_thd": 340,
    "total_kwh": 342,
    "total_kvarh": 344,
    "l1_import_kwh": 346,
    "l2_import_kwh": 348,
    "l3_import_kwh": 350,
    "l1_export_kwh": 352,
    "l2_export_kwh": 354,
    "l3_export_kwh": 356,
    "l1_total_kwh": 358,
    "l2_total_kwh": 360,
    "l3_total_kwh": 362,
    "l1_import_kvarh": 364,
    "l2_import_kvarh": 366,
    "l3_import_kvarh": 368,
    "l1_export_kvarh": 370,
    "l2_export_kvarh": 372,
    "l3_export_kvarh": 374,
    "l1_total_kvarh": 376,
    "l2_total_kvarh": 378,
    "l3_total_kvarh": 380,
}
