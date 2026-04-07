"""Test setup for lightweight Home Assistant/pymodbus stubs."""

from __future__ import annotations

import sys
import types
from enum import StrEnum
from pathlib import Path

# Ensure repository root is importable when tests run in constrained environments.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_homeassistant_stubs() -> None:
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    const = types.ModuleType("homeassistant.const")
    core = types.ModuleType("homeassistant.core")

    class ConfigEntry:  # pragma: no cover
        pass

    class Platform(StrEnum):
        SENSOR = "sensor"

    class HomeAssistant:  # pragma: no cover
        pass

    config_entries.ConfigEntry = ConfigEntry  # type: ignore[attr-defined]
    const.CONF_HOST = "host"  # type: ignore[attr-defined]
    const.CONF_PORT = "port"  # type: ignore[attr-defined]
    const.Platform = Platform  # type: ignore[attr-defined]
    core.HomeAssistant = HomeAssistant  # type: ignore[attr-defined]

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.const"] = const
    sys.modules["homeassistant.core"] = core


def _ensure_pymodbus_stubs() -> None:
    if "pymodbus" in sys.modules:
        return

    pymodbus = types.ModuleType("pymodbus")
    client = types.ModuleType("pymodbus.client")
    framer = types.ModuleType("pymodbus.framer")

    class AsyncModbusTcpClient:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            self.connected = False

        async def connect(self):
            self.connected = True

        def close(self):
            self.connected = False

    class ModbusRtuFramer:  # pragma: no cover
        pass

    class ModbusSocketFramer:  # pragma: no cover
        pass

    client.AsyncModbusTcpClient = AsyncModbusTcpClient  # type: ignore[attr-defined]
    framer.FramerRTU = ModbusRtuFramer  # type: ignore[attr-defined]
    framer.FramerSocket = ModbusSocketFramer  # type: ignore[attr-defined]

    sys.modules["pymodbus"] = pymodbus
    sys.modules["pymodbus.client"] = client
    sys.modules["pymodbus.framer"] = framer


_ensure_homeassistant_stubs()
_ensure_pymodbus_stubs()
