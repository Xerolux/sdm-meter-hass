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

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the SDM Meter sensor platform."""
    hub = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        """Fetch data from Modbus."""
        data = {}

        # Batch ranges based on standard modbus register limits (usually max 125 registers per read)
        # SENSOR_ADDRESSES contains addresses spanning from 0 to ~380.
        # We group them into chunks.
        addresses = sorted(SENSOR_ADDRESSES.values())
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
        for start_addr, count in chunks:
            registers = await hub.read_input_registers(start_addr, count)
            if not registers:
                _LOGGER.error("Failed to read chunk starting at %s", start_addr)
                continue

            for key, addr in SENSOR_ADDRESSES.items():
                if start_addr <= addr < start_addr + count:
                    index = addr - start_addr
                    val = hub.decode_float32(registers, index)
                    data[key] = val

        return data

    update_interval_sec = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SDM Meter",
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval_sec),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for description in SENSOR_TYPES:
        entities.append(SdmMeterSensor(coordinator, description, entry.entry_id))

    async_add_entities(entities)

class SdmMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SDM Meter sensor."""

    def __init__(self, coordinator, description, entry_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is not None and hasattr(self.entity_description, 'precision'):
            return round(val, self.entity_description.precision)
        return val

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id.split('_')[0])},
            "name": "SDM Meter",
            "manufacturer": "Eastron",
            "model": "SDM630",
        }

from dataclasses import dataclass
from homeassistant.components.sensor import SensorEntityDescription

@dataclass(frozen=True, kw_only=True)
class SdmSensorEntityDescription(SensorEntityDescription):
    """Class describing SDM sensor entities."""
    precision: int = 2

SENSOR_TYPES = [
    SdmSensorEntityDescription(
        key="waermepumpe_l1_neutral_volts",
        name="Phase 1 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_neutral_volts",
        name="Phase 2 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_neutral_volts",
        name="Phase 3 Spannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_current",
        name="Phase 1 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_current",
        name="Phase 2 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_current",
        name="Phase 3 Strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_power",
        name="Phase 1 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_power",
        name="Phase 2 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_power",
        name="Phase 3 Wirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_volt_amps",
        name="Phase 1 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_volt_amps",
        name="Phase 2 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_volt_amps",
        name="Phase 3 Scheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_volt_amps_reactive",
        name="Phase 1 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_volt_amps_reactive",
        name="Phase 2 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_volt_amps_reactive",
        name="Phase 3 Blindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_power_factor",
        name="Phase 1 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_power_factor",
        name="Phase 2 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_power_factor",
        name="Phase 3 Leistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_phase_angle",
        name="Phase 1 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_phase_angle",
        name="Phase 2 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_phase_angle",
        name="Phase 3 Phasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_average_line_neutral_volt",
        name="Durchschnittsspannung L-N",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_average_line_current",
        name="Durchschnittsstrom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_sum_line_currents",
        name="Stromsumme",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_system_power",
        name="Gesamtwirkleistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_system_volt_amps",
        name="Gesamtscheinleistung",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_system_var",
        name="Gesamtblindleistung",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_system_power_factor",
        name="Gesamtleistungsfaktor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        precision=3,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_system_phase_angle",
        name="Gesamtphasenwinkel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_frequency",
        name="Netzfrequenz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Hz",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_import_kwh",
        name="Bezug Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_export_kwh",
        name="Einspeisung Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_import_varh",
        name="Bezug Blindleistung",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_export_varh",
        name="Einspeisung Blindleistung",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_vah_total",
        name="Scheinleistung Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvah",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_ah_total",
        name="Stromsumme Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Ah",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_power_demand",
        name="Wirkleistungsbedarf",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_power_demand",
        name="Maximaler Wirkleistungsbedarf",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_va_demand",
        name="Scheinleistungsbedarf",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_va_demand",
        name="Maximaler Scheinleistungsbedarf",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        precision=0,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_neutral_current_demand",
        name="Neutralstrom Bedarf",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_neutral_current_demand",
        name="Maximaler Neutralstrom Bedarf",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_line1_line2_volts",
        name="Spannung L1-L2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_line2_line3_volts",
        name="Spannung L2-L3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_line3_line1_volts",
        name="Spannung L3-L1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_avg_line_line_volts",
        name="Durchschnittsspannung L-L",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        precision=1,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_neutral_current",
        name="Neutralstrom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_volts_thd",
        name="THD Spannung L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_volts_thd",
        name="THD Spannung L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_volts_thd",
        name="THD Spannung L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_current_thd",
        name="THD Strom L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_current_thd",
        name="THD Strom L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_current_thd",
        name="THD Strom L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_avg_volts_thd",
        name="THD Spannung Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_avg_current_thd",
        name="THD Strom Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_current_demand",
        name="Strombedarf L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_current_demand",
        name="Strombedarf L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_current_demand",
        name="Strombedarf L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_l1_current_demand",
        name="Max Strombedarf L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_l2_current_demand",
        name="Max Strombedarf L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_max_l3_current_demand",
        name="Max Strombedarf L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1l2_volts_thd",
        name="THD Spannung L1-L2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2l3_volts_thd",
        name="THD Spannung L2-L3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3l1_volts_thd",
        name="THD Spannung L3-L1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_avg_line_line_volts_thd",
        name="THD Spannung L-L Durchschnitt",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_kwh",
        name="Energie Gesamt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_total_kvarh",
        name="Blindleistung Gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_import_kwh",
        name="Bezug L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_import_kwh",
        name="Bezug L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_import_kwh",
        name="Bezug L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_export_kwh",
        name="Einspeisung L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_export_kwh",
        name="Einspeisung L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_export_kwh",
        name="Einspeisung L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_total_kwh",
        name="Energie Gesamt L1",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_total_kwh",
        name="Energie Gesamt L2",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_total_kwh",
        name="Energie Gesamt L3",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_import_kvarh",
        name="Bezug Blindleistung L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_import_kvarh",
        name="Bezug Blindleistung L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_import_kvarh",
        name="Bezug Blindleistung L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_export_kvarh",
        name="Einspeisung Blindleistung L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_export_kvarh",
        name="Einspeisung Blindleistung L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_export_kvarh",
        name="Einspeisung Blindleistung L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l1_total_kvarh",
        name="Blindleistung Gesamt L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l2_total_kvarh",
        name="Blindleistung Gesamt L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
    SdmSensorEntityDescription(
        key="waermepumpe_l3_total_kvarh",
        name="Blindleistung Gesamt L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kvarh",
        precision=2,
    ),
]

SENSOR_ADDRESSES = {
    "waermepumpe_l1_neutral_volts": 0,
    "waermepumpe_l2_neutral_volts": 2,
    "waermepumpe_l3_neutral_volts": 4,
    "waermepumpe_l1_current": 6,
    "waermepumpe_l2_current": 8,
    "waermepumpe_l3_current": 10,
    "waermepumpe_l1_power": 12,
    "waermepumpe_l2_power": 14,
    "waermepumpe_l3_power": 16,
    "waermepumpe_l1_volt_amps": 18,
    "waermepumpe_l2_volt_amps": 20,
    "waermepumpe_l3_volt_amps": 22,
    "waermepumpe_l1_volt_amps_reactive": 24,
    "waermepumpe_l2_volt_amps_reactive": 26,
    "waermepumpe_l3_volt_amps_reactive": 28,
    "waermepumpe_l1_power_factor": 30,
    "waermepumpe_l2_power_factor": 32,
    "waermepumpe_l3_power_factor": 34,
    "waermepumpe_l1_phase_angle": 36,
    "waermepumpe_l2_phase_angle": 38,
    "waermepumpe_l3_phase_angle": 40,
    "waermepumpe_average_line_neutral_volt": 42,
    "waermepumpe_average_line_current": 46,
    "waermepumpe_sum_line_currents": 48,
    "waermepumpe_total_system_power": 52,
    "waermepumpe_total_system_volt_amps": 56,
    "waermepumpe_total_system_var": 60,
    "waermepumpe_total_system_power_factor": 62,
    "waermepumpe_total_system_phase_angle": 66,
    "waermepumpe_frequency": 70,
    "waermepumpe_import_kwh": 72,
    "waermepumpe_export_kwh": 74,
    "waermepumpe_import_varh": 76,
    "waermepumpe_export_varh": 78,
    "waermepumpe_vah_total": 80,
    "waermepumpe_ah_total": 82,
    "waermepumpe_power_demand": 84,
    "waermepumpe_max_power_demand": 86,
    "waermepumpe_va_demand": 100,
    "waermepumpe_max_va_demand": 102,
    "waermepumpe_neutral_current_demand": 104,
    "waermepumpe_max_neutral_current_demand": 106,
    "waermepumpe_line1_line2_volts": 200,
    "waermepumpe_line2_line3_volts": 202,
    "waermepumpe_line3_line1_volts": 204,
    "waermepumpe_avg_line_line_volts": 206,
    "waermepumpe_neutral_current": 224,
    "waermepumpe_l1_volts_thd": 234,
    "waermepumpe_l2_volts_thd": 236,
    "waermepumpe_l3_volts_thd": 238,
    "waermepumpe_l1_current_thd": 240,
    "waermepumpe_l2_current_thd": 242,
    "waermepumpe_l3_current_thd": 244,
    "waermepumpe_avg_volts_thd": 248,
    "waermepumpe_avg_current_thd": 250,
    "waermepumpe_l1_current_demand": 258,
    "waermepumpe_l2_current_demand": 260,
    "waermepumpe_l3_current_demand": 262,
    "waermepumpe_max_l1_current_demand": 264,
    "waermepumpe_max_l2_current_demand": 266,
    "waermepumpe_max_l3_current_demand": 268,
    "waermepumpe_l1l2_volts_thd": 334,
    "waermepumpe_l2l3_volts_thd": 336,
    "waermepumpe_l3l1_volts_thd": 338,
    "waermepumpe_avg_line_line_volts_thd": 340,
    "waermepumpe_total_kwh": 342,
    "waermepumpe_total_kvarh": 344,
    "waermepumpe_l1_import_kwh": 346,
    "waermepumpe_l2_import_kwh": 348,
    "waermepumpe_l3_import_kwh": 350,
    "waermepumpe_l1_export_kwh": 352,
    "waermepumpe_l2_export_kwh": 354,
    "waermepumpe_l3_export_kwh": 356,
    "waermepumpe_l1_total_kwh": 358,
    "waermepumpe_l2_total_kwh": 360,
    "waermepumpe_l3_total_kwh": 362,
    "waermepumpe_l1_import_kvarh": 364,
    "waermepumpe_l2_import_kvarh": 366,
    "waermepumpe_l3_import_kvarh": 368,
    "waermepumpe_l1_export_kvarh": 370,
    "waermepumpe_l2_export_kvarh": 372,
    "waermepumpe_l3_export_kvarh": 374,
    "waermepumpe_l1_total_kvarh": 376,
    "waermepumpe_l2_total_kvarh": 378,
    "waermepumpe_l3_total_kvarh": 380,
}
