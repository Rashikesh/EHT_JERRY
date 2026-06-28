# backend/plc_connector.py
"""
PLC Connector: Demonstrates how to connect to real industrial PLCs
via Modbus TCP (the most common industrial protocol).
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
    
    async def connect(self):
        """Establish connection to the PLC"""
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
        """Read gas level from PLC holding register"""
        if not self.connected:
            return 0.0
        
        try:
            # Read 1 register (16-bit value)
            result = await self.client.read_holding_registers(
                address=register,
                count=1,
                slave=unit
            )
            if not result.isError():
                # Convert raw register value to engineering units
                # (e.g., divide by 100 to get percentage)
                raw_value = result.registers[0]
                return raw_value / 100.0
        except Exception as e:
            logger.error(f"Modbus read error: {e}")
        
        return 0.0
    
    async def read_pressure_sensor(self, register: int = 1, unit: int = 1) -> float:
        """Read pressure from PLC"""
        if not self.connected:
            return 0.0
        
        try:
            result = await self.client.read_holding_registers(
                address=register, count=1, slave=unit
            )
            if not result.isError():
                return result.registers[0] / 10.0  # Scale to bar
        except Exception as e:
            logger.error(f"Modbus read error: {e}")
        
        return 0.0
    
    async def close_valve(self, coil: int = 0, unit: int = 1):
        """Send command to PLC to close isolation valve"""
        if not self.connected:
            return False
        
        try:
            # Write to a coil (digital output) on the PLC
            result = await self.client.write_coil(
                address=coil, 
                value=True,  # True = close valve
                slave=unit
            )
            if not result.isError():
                logger.info(f"🚨 VALVE CLOSE command sent to PLC coil {coil}")
                return True
        except Exception as e:
            logger.error(f"Modbus write error: {e}")
        
        return False
    
    async def disconnect(self):
        """Close connection to PLC"""
        if self.connected:
            self.client.close()
            self.connected = False
            logger.info("🔌 Disconnected from PLC")


# Example usage in main.py
async def poll_plc_data(plc: PLCConnector, mqtt_client):
    """Continuously read from PLC and publish to MQTT"""
    while True:
        gas = await plc.read_gas_sensor(register=0)
        pressure = await plc.read_pressure_sensor(register=1)
        
        # Publish to MQTT (same as your mock sensor)
        import json
        mqtt_client.publish("factory/zone-a/gas", json.dumps({"value": gas}))
        mqtt_client.publish("factory/zone-a/pressure", json.dumps({"value": pressure}))
        
        await asyncio.sleep(2)