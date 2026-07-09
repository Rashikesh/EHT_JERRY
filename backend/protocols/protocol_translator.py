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

from protocols.plc_connector import PLCConnector  # 🆕 real Modbus implementation

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
    id: str
    name: str
    protocol: ProtocolType
    lat: float
    lng: float
    site_id: str = "site-a"  # 🆕 every asset now belongs to a site
    status: SensorStatus = SensorStatus.LEARNING

    mqtt_topic: Optional[str] = None
    modbus_host: Optional[str] = None       # 🆕 was hardcoded to localhost before
    modbus_port: int = 502                   # 🆕
    modbus_address: Optional[int] = None
    modbus_register: Optional[int] = None
    modbus_metric: str = "gas"               # 🆕 "gas" | "pressure" | "temperature"

    readings: List[float] = field(default_factory=list)
    learned_baseline: float = 0.0
    learned_threshold: float = 0.0
    learned_std: float = 0.0

    current_value: float = 0.0
    last_updated: float = 0.0
    learning_window: int = 30

    def add_reading(self, value: float):
        self.readings.append(value)
        self.current_value = value
        self.last_updated = time.time()

        if len(self.readings) > 100:
            self.readings = self.readings[-100:]

        if self.status == SensorStatus.LEARNING:
            if len(self.readings) >= self.learning_window:
                self._calculate_baseline()
                self.status = SensorStatus.ACTIVE
                logger.info(f"✅ Asset {self.name} completed learning. Baseline: {self.learned_baseline:.1f}, Threshold: {self.learned_threshold:.1f}")

        if self.status == SensorStatus.ACTIVE and self.current_value > self.learned_threshold:
            self.status = SensorStatus.CRITICAL
        elif self.status == SensorStatus.CRITICAL and self.current_value <= self.learned_threshold:
            self.status = SensorStatus.ACTIVE

    def _calculate_baseline(self):
        import statistics
        self.learned_baseline = statistics.mean(self.readings)
        self.learned_std = statistics.stdev(self.readings) if len(self.readings) > 1 else 0
        self.learned_threshold = self.learned_baseline + (2 * self.learned_std)
        self.learned_threshold = max(self.learned_threshold, self.learned_baseline * 1.1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "site_id": self.site_id,
            "lat": self.lat,
            "lng": self.lng,
            "status": self.status.value,
            "gasLevel": round(self.current_value, 1),
            "learnedThreshold": round(self.learned_threshold, 1),
            "learnedBaseline": round(self.learned_baseline, 1),
            "protocol": self.protocol.value,
            "readingCount": len(self.readings),
        }


class ProtocolTranslator:
    """Central hub that manages all IoT connections and normalizes their data."""

    def __init__(self):
        self.assets: Dict[str, IoTAsset] = {}
        self.mqtt_client = None
        self.mqtt_connected = False
        self.on_data_callback: Optional[Callable] = None
        logger.info("🔌 Protocol Translator initialized")

    async def provision_asset(self, asset: IoTAsset):
        self.assets[asset.id] = asset
        logger.info(f"📡 Provisioned new asset: {asset.name} ({asset.protocol.value}) [site={asset.site_id}]")

        if asset.protocol == ProtocolType.MQTT:
            await self._subscribe_mqtt(asset)
        elif asset.protocol == ProtocolType.MODBUS:
            await self._start_modbus_polling(asset)
        elif asset.protocol == ProtocolType.SIMULATED:
            await self._start_simulated_feed(asset)

        return asset.to_dict()

    async def _subscribe_mqtt(self, asset: IoTAsset):
        try:
            import paho.mqtt.client as mqtt

            if not self.mqtt_client:
                # 🔧 FIXED: explicit callback_api_version required for paho-mqtt 2.x
                self.mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

                def on_connect(client, userdata, flags, rc):
                    self.mqtt_connected = True
                    logger.info("✅ MQTT Broker connected")
                    for a in self.assets.values():
                        if a.protocol == ProtocolType.MQTT and a.mqtt_topic:
                            client.subscribe(a.mqtt_topic)

                def on_message(client, userdata, msg):
                    try:
                        payload = json.loads(msg.payload.decode())
                        value = payload.get("value", payload.get("gas", 0))
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
            logger.warning("⚠️ paho-mqtt not installed.")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")

    async def _start_modbus_polling(self, asset: IoTAsset):
        """🔧 FIXED: now uses the real PLCConnector, real per-asset host, and reads
        the metric this asset is actually configured for (gas/pressure/temperature) —
        instead of a hardcoded localhost:502 raw pymodbus client reading only 'gas'."""
        host = asset.modbus_host or "localhost"
        port = asset.modbus_port or 502

        plc = PLCConnector(host=host, port=port)
        connected = await plc.connect()

        if not connected:
            logger.warning(f"⚠️ Modbus connection failed for {asset.name} at {host}:{port}")
            asset.status = SensorStatus.OFFLINE
            return

        logger.info(f"📡 Modbus connected for asset: {asset.name} ({host}:{port})")

        async def poll_modbus():
            while asset.id in self.assets:
                try:
                    register = asset.modbus_register or 0
                    unit = asset.modbus_address or 1

                    if asset.modbus_metric == "pressure":
                        value = await plc.read_pressure_sensor(register=register, unit=unit)
                    elif asset.modbus_metric == "temperature":
                        value = await plc.read_temperature_sensor(register=register, unit=unit)
                    else:
                        value = await plc.read_gas_sensor(register=register, unit=unit)

                    asset.add_reading(value)
                    if self.on_data_callback:
                        await self.on_data_callback(asset)

                except Exception as e:
                    # Never let one bad read kill the polling loop
                    logger.error(f"Modbus read error for {asset.name}: {e}")

                await asyncio.sleep(2)

            await plc.disconnect()

        asyncio.create_task(poll_modbus())

    async def _start_simulated_feed(self, asset: IoTAsset):
        import random

        async def simulate():
            while asset.id in self.assets:
                noise = random.gauss(0, 2)
                value = max(0, min(100, 15 + noise))
                asset.add_reading(value)
                if self.on_data_callback:
                    await self.on_data_callback(asset)
                await asyncio.sleep(2)

        asyncio.create_task(simulate())
        logger.info(f"🎮 Started simulated feed for: {asset.name}")

    def get_all_assets(self) -> List[dict]:
        return [asset.to_dict() for asset in self.assets.values()]

    def get_assets_for_site(self, site_id: str) -> List[dict]:  # 🆕
        return [a.to_dict() for a in self.assets.values() if a.site_id == site_id]

    def get_asset(self, asset_id: str) -> Optional[dict]:
        asset = self.assets.get(asset_id)
        return asset.to_dict() if asset else None

    def remove_asset(self, asset_id: str) -> bool:
        if asset_id in self.assets:
            del self.assets[asset_id]
            logger.info(f"🗑️ Removed asset: {asset_id}")
            return True
        return False


translator = ProtocolTranslator()