import logging
import asyncio
import struct
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer

from homeassistant.core import HomeAssistant
from .const import CONF_HOST, CONF_PORT, CONF_SLAVE, CONF_CONNECTION_TYPE, CONN_RTU_OVER_TCP

_LOGGER = logging.getLogger(__name__)

class SdmMeterHub:
    """Modbus hub for SDM Meter."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, slave: int, connection_type: str = CONN_RTU_OVER_TCP):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._host = host
        self._port = port
        self._slave = slave

        framer = ModbusRtuFramer if connection_type == CONN_RTU_OVER_TCP else ModbusSocketFramer

        self._client = AsyncModbusTcpClient(
            host=self._host,
            port=self._port,
            framer=framer,
            timeout=10,
        )
        self._lock = asyncio.Lock()

    async def connect(self):
        """Connect to the Modbus server."""
        if not self._client.connected:
            await self._client.connect()

    async def close(self):
        """Close the Modbus connection."""
        if self._client.connected:
            self._client.close()

    async def read_input_registers(self, address: int, count: int):
        """Read input registers."""
        async with self._lock:
            await self.connect()
            if not self._client.connected:
                _LOGGER.error("Failed to connect to Modbus server %s:%s", self._host, self._port)
                return None
            try:
                result = await self._client.read_input_registers(
                    address=address,
                    count=count,
                    slave=self._slave
                )
                if result.isError():
                    _LOGGER.error("Modbus error reading address %s: %s", address, result)
                    return None
                return result.registers
            except Exception as e:
                _LOGGER.error("Exception reading Modbus address %s: %s", address, e)
                return None

    async def read_float32(self, address: int):
        """Read a float32 value from 2 input registers."""
        registers = await self.read_input_registers(address, 2)
        if not registers or len(registers) < 2:
            return None

        # Standard Modbus Float32 is often 2 registers.
        # SDM meters typically use IEEE 754 float32 Big Endian, CDAB or ABCD byte order
        # Usually it's read as 2 16-bit ints, packed into bytes, then unpacked as float
        try:
            # Assuming AB CD (Big Endian)
            b = struct.pack('>HH', registers[0], registers[1])
            val = struct.unpack('>f', b)[0]
            return val
        except Exception as e:
            _LOGGER.error("Error unpacking float at address %s: %s", address, e)
            return None

    def decode_float32(self, registers: list[int], index: int):
        """Decode a float32 value from a list of registers at a specific index."""
        if not registers or len(registers) < index + 2:
            return None

        try:
            b = struct.pack('>HH', registers[index], registers[index + 1])
            val = struct.unpack('>f', b)[0]
            return val
        except Exception as e:
            _LOGGER.error("Error unpacking float from registers at index %s: %s", index, e)
            return None
