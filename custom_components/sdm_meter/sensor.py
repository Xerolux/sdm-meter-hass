"""Sensor platform for SDM Meter integration."""
import logging
from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, CONF_MODEL, MODEL_SDM120

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the SDM Meter sensor platform."""
    hub = hass.data[DOMAIN][entry.entry_id]

    model_name = entry.data.get(CONF_MODEL)

    def is_supported(key: str) -> bool:
        """Check if a sensor key is supported by the current model."""
        if model_name == MODEL_SDM120:
            # Filter out 3-phase specific registers for 1-phase meters
            if "l2" in key or "l3" in key or "line" in key:
                return False
            # Exclude aggregate system values which are essentially duplicates or invalid on 1-phase
            if "total_system" in key or "sum_" in key or "avg_" in key or "average_" in key:
                return False
            if key.startswith("l1_") and key != "l1_neutral_volts" and key != "l1_current" and key != "l1_power":
                # SDM120 usually just provides total values instead of L1 specific values for energy
                if "kwh" in key or "kvarh" in key or "thd" in key or "demand" in key:
                    return False
        return True

    supported_addresses = {k: v for k, v in SENSOR_ADDRESSES.items() if is_supported(k)}

    async def async_update_data():
        """Fetch data from Modbus."""
        data = {}

        # Batch ranges based on standard modbus register limits (usually max 125 registers per read)
        # SENSOR_ADDRESSES contains addresses spanning from 0 to ~380.
        # We group them into chunks.
        addresses = sorted(supported_addresses.values())
        if not addresses:
            return data

        chunks = []
        current_start = addresses[0]
        current_end = current_start + 2

        for addr in addresses[1:]:
            # If the next address is within 60 registers (120 bytes) of the start, extend the chunk
            # Max registers per read is typically ~120
            if addr + 2 - current_start <= 100:
                current_end = max(current_end, addr + 2)
            else:
                chunks.append((current_start, current_end - current_start))
                current_start = addr
                current_end = addr + 2
        chunks.append((current_start, current_end - current_start))

        # Read chunks and populate data
        success_count = 0
        for start_addr, count in chunks:
            registers = await hub.read_input_registers(start_addr, count)
            if not registers:
                _LOGGER.warning("Failed to read chunk starting at %s", start_addr)
                continue

            success_count += 1
            for key, addr in supported_addresses.items():
                if start_addr <= addr < start_addr + count:
                    index = addr - start_addr
                    val = hub.decode_float32(registers, index)
                    data[key] = val

        if success_count == 0:
            raise UpdateFailed("Failed to read any data from Modbus meter")

        return data

    update_interval_sec = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    name = entry.data.get("name", "SDM Meter")
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval_sec),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for description in SENSOR_TYPES:
        if is_supported(description.key):
            entities.append(SdmMeterSensor(coordinator, description, entry))

    async_add_entities(entities)

class SdmMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SDM Meter sensor."""

    def __init__(self, coordinator, description, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._device_name = entry.data.get("name", "SDM Meter")
        self._entry_id = entry.entry_id
        self._model = entry.data.get(CONF_MODEL, "SDM630")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is not None and hasattr(self.entity_description, 'precision'):
            if self.entity_description.precision == 0:
                return int(round(val, 0))
            return round(val, self.entity_description.precision)
        return val

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Eastron",
            "model": self._model,
        }

from dataclasses import dataclass
from homeassistant.components.sensor import SensorEntityDescription

@dataclass(frozen=True, kw_only=True)
class SdmSensorEntityDescription(SensorEntityDescription):
    """Class describing SDM sensor entities."""
    precision: int = 2

SENSOR_TYPES = [
    SdmSensorEntityDescription(
        key="l1_neutral_volts",
        name="Phase 1 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="l2_neutral_volts",
        name="Phase 2 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="l3_neutral_volts",
        name="Phase 3 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="l1_current",
        name="Phase 1 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_current",
        name="Phase 2 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_current",
        name="Phase 3 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_power",
        name="Phase 1 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l2_power",
        name="Phase 2 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l3_power",
        name="Phase 3 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l1_volt_amps",
        name="Phase 1 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l2_volt_amps",
        name="Phase 2 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l3_volt_amps",
        name="Phase 3 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l1_volt_amps_reactive",
        name="Phase 1 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l2_volt_amps_reactive",
        name="Phase 2 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l3_volt_amps_reactive",
        name="Phase 3 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="l1_power_factor",
        name="Phase 1 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="l2_power_factor",
        name="Phase 2 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="l3_power_factor",
        name="Phase 3 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="l1_phase_angle",
        name="Phase 1 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="l2_phase_angle",
        name="Phase 2 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="l3_phase_angle",
        name="Phase 3 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="average_line_neutral_volt",
        name="Durchschnittsspannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="average_line_current",
        name="Durchschnittsstrom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="sum_line_currents",
        name="Stromsumme",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="total_system_power",
        name="Gesamtwirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="total_system_volt_amps",
        name="Gesamtscheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="total_system_var",
        name="Gesamtblindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="total_system_power_factor",
        name="Gesamtleistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="total_system_phase_angle",
        name="Gesamtphasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="frequency",
        name="Netzfrequenz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Hz",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="import_kwh",
        name="Bezug Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="export_kwh",
        name="Einspeisung Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="import_varh",
        name="Bezug Blindleistung",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="export_varh",
        name="Einspeisung Blindleistung",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="vah_total",
        name="Scheinleistung Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvah",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="ah_total",
        name="Stromsumme Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Ah",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="power_demand",
        name="Wirkleistungsbedarf",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="max_power_demand",
        name="Maximaler Wirkleistungsbedarf",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="va_demand",
        name="Scheinleistungsbedarf",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="max_va_demand",
        name="Maximaler Scheinleistungsbedarf",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="neutral_current_demand",
        name="Neutralstrom Bedarf",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="max_neutral_current_demand",
        name="Maximaler Neutralstrom Bedarf",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="line1_line2_volts",
        name="Spannung L1-L2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="line2_line3_volts",
        name="Spannung L2-L3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="line3_line1_volts",
        name="Spannung L3-L1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="avg_line_line_volts",
        name="Durchschnittsspannung L-L",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="neutral_current",
        name="Neutralstrom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_volts_thd",
        name="THD Spannung L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_volts_thd",
        name="THD Spannung L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_volts_thd",
        name="THD Spannung L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_current_thd",
        name="THD Strom L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_current_thd",
        name="THD Strom L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_current_thd",
        name="THD Strom L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="avg_volts_thd",
        name="THD Spannung Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="avg_current_thd",
        name="THD Strom Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_current_demand",
        name="Strombedarf L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_current_demand",
        name="Strombedarf L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_current_demand",
        name="Strombedarf L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="max_l1_current_demand",
        name="Max Strombedarf L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="max_l2_current_demand",
        name="Max Strombedarf L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="max_l3_current_demand",
        name="Max Strombedarf L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1l2_volts_thd",
        name="THD Spannung L1-L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2l3_volts_thd",
        name="THD Spannung L2-L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3l1_volts_thd",
        name="THD Spannung L3-L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="avg_line_line_volts_thd",
        name="THD Spannung L-L Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="total_kwh",
        name="Energie Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="total_kvarh",
        name="Blindleistung Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_import_kwh",
        name="Bezug L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_import_kwh",
        name="Bezug L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_import_kwh",
        name="Bezug L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_export_kwh",
        name="Einspeisung L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_export_kwh",
        name="Einspeisung L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_export_kwh",
        name="Einspeisung L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_total_kwh",
        name="Energie Gesamt L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_total_kwh",
        name="Energie Gesamt L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_total_kwh",
        name="Energie Gesamt L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_import_kvarh",
        name="Bezug Blindleistung L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_import_kvarh",
        name="Bezug Blindleistung L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_import_kvarh",
        name="Bezug Blindleistung L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_export_kvarh",
        name="Einspeisung Blindleistung L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_export_kvarh",
        name="Einspeisung Blindleistung L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_export_kvarh",
        name="Einspeisung Blindleistung L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l1_total_kvarh",
        name="Blindleistung Gesamt L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l2_total_kvarh",
        name="Blindleistung Gesamt L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="l3_total_kvarh",
        name="Blindleistung Gesamt L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
]

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
