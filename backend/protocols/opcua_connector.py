# backend/opcua_connector.py
"""
OPC UA Connector: For modern SCADA systems (Siemens WinCC, Wonderware, etc.)
"""
from asyncua import Client
import asyncio

class OPCUAConnector:
    """Connects to SCADA systems via OPC UA (IEC 62541 standard)"""
    
    def __init__(self, url: str = "opc.tcp://localhost:4840"):
        self.url = url
        self.client = Client(url)
    
    async def connect(self):
        try:
            await self.client.connect()
            print(f"✅ Connected to OPC UA server at {self.url}")
        except Exception as e:
            print(f"❌ OPC UA connection failed: {e}")
    
    async def read_sensor(self, node_id: str = "ns=2;s=GasLevel"):
        """Read a sensor value from OPC UA node"""
        try:
            node = self.client.get_node(node_id)
            value = await node.read_value()
            return value
        except Exception as e:
            print(f"OPC UA read error: {e}")
            return 0.0
    
    async def write_command(self, node_id: str, value):
        """Send command to SCADA system"""
        try:
            node = self.client.get_node(node_id)
            await node.write_value(value)
            print(f"🚨 Command sent to OPC UA node {node_id}")
        except Exception as e:
            print(f"OPC UA write error: {e}")