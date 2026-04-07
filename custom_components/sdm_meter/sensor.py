"""Sensor platform for SDM Meter integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_MODEL, CONF_NAME, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .descriptions import SENSOR_TYPES
from .register_map import (
    build_register_chunks,
    get_supported_addresses,
    is_sensor_supported_for_model,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SDM Meter sensor platform."""
    hub = hass.data[DOMAIN][entry.entry_id]
    model_name = entry.data.get(CONF_MODEL)
    supported_addresses = get_supported_addresses(model_name)

    async def async_update_data() -> dict[str, float | None]:
        """Fetch data from Modbus."""
        data: dict[str, float | None] = {}

        addresses = sorted(supported_addresses.values())
        for start_addr, count in build_register_chunks(addresses):
            registers = await hub.read_input_registers(start_addr, count)
            if not registers:
                _LOGGER.warning("Failed to read chunk starting at %s", start_addr)
                continue

            for key, address in supported_addresses.items():
                if start_addr <= address < start_addr + count:
                    index = address - start_addr
                    data[key] = hub.decode_float32(registers, index)

        if not data:
            raise UpdateFailed("Failed to read any data from Modbus meter")

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=entry.data.get(CONF_NAME, "SDM Meter"),
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        SdmMeterSensor(coordinator, description, entry)
        for description in SENSOR_TYPES
        if is_sensor_supported_for_model(model_name, description.key)
    ]
    async_add_entities(entities)


class SdmMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SDM Meter sensor."""

    def __init__(self, coordinator, description, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._device_name = entry.data.get(CONF_NAME, "SDM Meter")
        self._model = entry.data.get(CONF_MODEL, "SDM630")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is not None and hasattr(self.entity_description, "precision"):
            if self.entity_description.precision == 0:
                return int(round(value, 0))
            return round(value, self.entity_description.precision)
        return value

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return super().available and self.entity_description.key in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="Eastron",
            model=self._model,
        )
