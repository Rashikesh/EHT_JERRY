"""
PLC Connector: Connects to real industrial PLCs via Modbus TCP.
"""
from pymodbus.client import AsyncModbusTcpClient
import asyncio
import logging

logger = logging.getLogger(__name__)


class PLCConnector:
    """Connects to real Siemens/Allen-Bradley/Schneider PLCs via Modbus TCP"""

    def __init__(self, host: str = "192.168.1.10", port: int = 502):
        self.host = host
        self.port = port
        self.client = AsyncModbusTcpClient(host, port=port)
        self.connected = False

    async def connect(self) -> bool:
        try:
            await self.client.connect()
            if self.client.connected:
                self.connected = True
                logger.info(f"✅ Connected to PLC at {self.host}:{self.port}")
                return True
        except Exception as e:
            logger.error(f"❌ PLC Connection failed: {e}")
        return False

    async def read_gas_sensor(self, register: int = 0, unit: int = 1) -> float:
        if not self.connected:
            return 0.0
        try:
            result = await self.client.read_holding_registers(address=register, count=1, slave=unit)
            if not result.isError():
                return result.registers[0] / 100.0
        except Exception as e:
            logger.error(f"Modbus read error (gas): {e}")
        return 0.0

    async def read_pressure_sensor(self, register: int = 1, unit: int = 1) -> float:
        if not self.connected:
            return 0.0
        try:
            result = await self.client.read_holding_registers(address=register, count=1, slave=unit)
            if not result.isError():
                return result.registers[0] / 10.0
        except Exception as e:
            logger.error(f"Modbus read error (pressure): {e}")
        return 0.0

    # 🆕 was missing entirely — broadcast_loop and permit_agent both need temperature
    async def read_temperature_sensor(self, register: int = 2, unit: int = 1) -> float:
        if not self.connected:
            return 0.0
        try:
            result = await self.client.read_holding_registers(address=register, count=1, slave=unit)
            if not result.isError():
                return result.registers[0] / 10.0
        except Exception as e:
            logger.error(f"Modbus read error (temperature): {e}")
        return 0.0

    async def close_valve(self, coil: int = 0, unit: int = 1) -> bool:
        if not self.connected:
            return False
        try:
            result = await self.client.write_coil(address=coil, value=True, slave=unit)
            if not result.isError():
                logger.info(f"🚨 VALVE CLOSE command sent to PLC coil {coil}")
                return True
        except Exception as e:
            logger.error(f"Modbus write error: {e}")
        return False

    async def disconnect(self):
        if self.connected:
            self.client.close()
            self.connected = False
            logger.info("🔌 Disconnected from PLC")