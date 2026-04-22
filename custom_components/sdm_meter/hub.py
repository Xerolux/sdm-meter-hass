"""Modbus hub for SDM Meter integration."""

from __future__ import annotations

import asyncio
import logging
import struct

from homeassistant.core import HomeAssistant
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer import FramerRTU, FramerSocket

from .const import CONN_RTU_OVER_TCP

_LOGGER = logging.getLogger(__name__)


class SdmMeterHub:
    """Modbus hub for SDM Meter."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave: int,
        connection_type: str = CONN_RTU_OVER_TCP,
    ) -> None:
        """Initialize the Modbus hub."""
        self._hass = hass
        self._host = host
        self._port = port
        self._slave = slave

        framer = (
            FramerRTU
            if connection_type == CONN_RTU_OVER_TCP
            else FramerSocket
        )

        self._client = AsyncModbusTcpClient(
            host=self._host,
            port=self._port,
            framer=framer,
            timeout=10,
        )
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        """Return whether the underlying Modbus client is connected."""
        return bool(self._client.connected)

    async def connect(self) -> bool:
        """Connect to the Modbus server."""
        if not self._client.connected:
            await self._client.connect()
        return self.connected

    async def close(self) -> None:
        """Close the Modbus connection."""
        if self._client.connected:
            self._client.close()

    # pylint: disable=broad-except
    async def read_input_registers(self, address: int, count: int) -> list[int] | None:
        """Read input registers."""
        async with self._lock:
            await self.connect()
            if not self._client.connected:
                _LOGGER.error(
                    "Failed to connect to Modbus server %s:%s",
                    self._host,
                    self._port,
                )
                return None
            try:
                result = await self._client.read_input_registers(
                    address=address,
                    count=count,
                    device_id=self._slave,
                )
                if result.isError():
                    _LOGGER.error("Modbus error reading address %s: %s", address, result)
                    return None
                return result.registers
            except Exception:
                _LOGGER.exception("Exception reading Modbus address %s", address)
                return None

    # pylint: disable=broad-except
    async def read_float32(self, address: int) -> float | None:
        """Read a float32 value from 2 input registers."""
        registers = await self.read_input_registers(address, 2)
        if not registers or len(registers) < 2:
            return None

        try:
            raw = struct.pack(">HH", registers[0], registers[1])
            return struct.unpack(">f", raw)[0]
        except Exception:
            _LOGGER.exception("Error unpacking float at address %s", address)
            return None

    # pylint: disable=broad-except
    def decode_float32(self, registers: list[int], index: int) -> float | None:
        """Decode a float32 value from a list of registers at a specific index."""
        if not registers or len(registers) < index + 2:
            return None

        try:
            raw = struct.pack(">HH", registers[index], registers[index + 1])
            return struct.unpack(">f", raw)[0]
        except Exception:
            _LOGGER.exception(
                "Error unpacking float from registers at index %s",
                index,
            )
            return None
