# backend/protocol_translator.py
"""
Protocol Translator: Converts MQTT and Modbus data into a unified format.
This is the core of the Plug-and-Play system.
"""
import asyncio
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class SensorStatus(Enum):
    LEARNING = "learning"
    ACTIVE = "active"
    CRITICAL = "critical"
    OFFLINE = "offline"

class ProtocolType(Enum):
    MQTT = "mqtt"
    MODBUS = "modbus"
    SIMULATED = "simulated"

@dataclass
class IoTAsset:
    """Represents a single IoT sensor/device in the system"""
    id: str
    name: str
    protocol: ProtocolType
    lat: float
    lng: float
    status: SensorStatus = SensorStatus.LEARNING
    
    # Connection details
    mqtt_topic: Optional[str] = None
    modbus_address: Optional[int] = None
    modbus_register: Optional[int] = None
    
    # Self-Harnessing AI Data
    readings: List[float] = field(default_factory=list)
    learned_baseline: float = 0.0
    learned_threshold: float = 0.0
    learned_std: float = 0.0
    
    # Current state
    current_value: float = 0.0
    last_updated: float = 0.0
    
    # Learning config
    learning_window: int = 30  # Number of readings before baseline is set
    
    def add_reading(self, value: float):
        """Add a new sensor reading and update baseline if in learning phase"""
        self.readings.append(value)
        self.current_value = value
        self.last_updated = time.time()
        
        # Keep only last 100 readings
        if len(self.readings) > 100:
            self.readings = self.readings[-100:]
        
        # Self-Harnessing: Calculate baseline during learning phase
        if self.status == SensorStatus.LEARNING:
            if len(self.readings) >= self.learning_window:
                self._calculate_baseline()
                self.status = SensorStatus.ACTIVE
                logger.info(f"✅ Asset {self.name} completed learning. Baseline: {self.learned_baseline:.1f}, Threshold: {self.learned_threshold:.1f}")
        
        # Check if current value exceeds learned threshold
        if self.status == SensorStatus.ACTIVE and self.current_value > self.learned_threshold:
            self.status = SensorStatus.CRITICAL
        elif self.status == SensorStatus.CRITICAL and self.current_value <= self.learned_threshold:
            self.status = SensorStatus.ACTIVE
    
    def _calculate_baseline(self):
        """Self-Harnessing: Calculate mean + 2*std as dynamic threshold"""
        import statistics
        self.learned_baseline = statistics.mean(self.readings)
        self.learned_std = statistics.stdev(self.readings) if len(self.readings) > 1 else 0
        # Dynamic threshold = baseline + 2 standard deviations
        self.learned_threshold = self.learned_baseline + (2 * self.learned_std)
        # Minimum threshold of baseline + 10%
        self.learned_threshold = max(self.learned_threshold, self.learned_baseline * 1.1)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "status": self.status.value,
            "gasLevel": round(self.current_value, 1),
            "learnedThreshold": round(self.learned_threshold, 1),
            "learnedBaseline": round(self.learned_baseline, 1),
            "protocol": self.protocol.value,
            "readingCount": len(self.readings)
        }


class ProtocolTranslator:
    """
    Central hub that manages all IoT connections.
    Accepts MQTT and Modbus devices and normalizes their data.
    """
    
    def __init__(self):
        self.assets: Dict[str, IoTAsset] = {}
        self.mqtt_client = None
        self.mqtt_connected = False
        self.on_data_callback: Optional[Callable] = None
        logger.info("🔌 Protocol Translator initialized")
    
    async def provision_asset(self, asset: IoTAsset):
        """Add a new IoT device to the system"""
        self.assets[asset.id] = asset
        logger.info(f"📡 Provisioned new asset: {asset.name} ({asset.protocol.value})")
        
        if asset.protocol == ProtocolType.MQTT:
            await self._subscribe_mqtt(asset)
        elif asset.protocol == ProtocolType.MODBUS:
            await self._start_modbus_polling(asset)
        elif asset.protocol == ProtocolType.SIMULATED:
            await self._start_simulated_feed(asset)
        
        return asset.to_dict()
    
    async def _subscribe_mqtt(self, asset: IoTAsset):
        """Subscribe to an MQTT topic for real sensor data"""
        try:
            import paho.mqtt.client as mqtt
            
            if not self.mqtt_client:
                self.mqtt_client = mqtt.Client()
                
                def on_connect(client, userdata, flags, rc):
                    self.mqtt_connected = True
                    logger.info("✅ MQTT Broker connected")
                    # Re-subscribe to all MQTT assets
                    for a in self.assets.values():
                        if a.protocol == ProtocolType.MQTT and a.mqtt_topic:
                            client.subscribe(a.mqtt_topic)
                
                def on_message(client, userdata, msg):
                    try:
                        payload = json.loads(msg.payload.decode())
                        value = payload.get("value", payload.get("gas", 0))
                        # Find which asset this topic belongs to
                        for a in self.assets.values():
                            if a.mqtt_topic == msg.topic:
                                a.add_reading(float(value))
                                if self.on_data_callback:
                                    asyncio.create_task(self.on_data_callback(a))
                    except Exception as e:
                        logger.error(f"MQTT parse error: {e}")
                
                self.mqtt_client.on_connect = on_connect
                self.mqtt_client.on_message = on_message
                self.mqtt_client.connect("localhost", 1883, 60)
                self.mqtt_client.loop_start()
            
            if asset.mqtt_topic:
                self.mqtt_client.subscribe(asset.mqtt_topic)
                logger.info(f"📡 Subscribed to MQTT topic: {asset.mqtt_topic}")
                
        except ImportError:
            logger.warning("⚠️ paho-mqtt not installed. Install with: pip install paho-mqtt")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
    
    async def _start_modbus_polling(self, asset: IoTAsset):
        """Start polling a Modbus TCP device"""
        try:
            from pymodbus.client import AsyncModbusTcpClient
            
            client = AsyncModbusTcpClient("localhost", port=502)
            await client.connect()
            
            if client.connected:
                logger.info(f"📡 Modbus connected for asset: {asset.name}")
                
                async def poll_modbus():
                    while asset.id in self.assets:
                        try:
                            result = await client.read_holding_registers(
                                address=asset.modbus_register or 0,
                                count=1,
                                slave=asset.modbus_address or 1
                            )
                            if not result.isError():
                                value = result.registers[0] / 10.0  # Scale factor
                                asset.add_reading(value)
                                if self.on_data_callback:
                                    await self.on_data_callback(asset)
                        except Exception as e:
                            logger.error(f"Modbus read error: {e}")
                        await asyncio.sleep(2)
                
                asyncio.create_task(poll_modbus())
            else:
                logger.warning(f"⚠️ Modbus connection failed for {asset.name}")
                
        except ImportError:
            logger.warning("⚠️ pymodbus not installed. Install with: pip install pymodbus")
        except Exception as e:
            logger.error(f"❌ Modbus error: {e}")
    
    async def _start_simulated_feed(self, asset: IoTAsset):
        """Generate simulated data for demo/testing purposes"""
        import random
        
        async def simulate():
            while asset.id in self.assets:
                # Simulate realistic sensor noise
                noise = random.gauss(0, 2)
                value = max(0, min(100, 15 + noise))  # Baseline around 15%
                asset.add_reading(value)
                
                if self.on_data_callback:
                    await self.on_data_callback(asset)
                
                await asyncio.sleep(2)
        
        asyncio.create_task(simulate())
        logger.info(f"🎮 Started simulated feed for: {asset.name}")
    
    def get_all_assets(self) -> List[dict]:
        """Return all provisioned assets as dictionaries"""
        return [asset.to_dict() for asset in self.assets.values()]
    
    def get_asset(self, asset_id: str) -> Optional[dict]:
        """Return a single asset by ID"""
        asset = self.assets.get(asset_id)
        return asset.to_dict() if asset else None
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the system"""
        if asset_id in self.assets:
            del self.assets[asset_id]
            logger.info(f"🗑️ Removed asset: {asset_id}")
            return True
        return False


# Global instance
translator = ProtocolTranslator()