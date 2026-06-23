# backend/protocol_translator.py
import time
import paho.mqtt.client as mqtt

class ProtocolTranslator:
    def __init__(self):
        # Initialize MQTT client (Handles both paho-mqtt v1.x and v2.x)
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.mqtt_client = mqtt.Client()
        
    def connect_mqtt(self, broker_ip: str, topic: str):
        """Plug-and-play connection to any MQTT sensor"""
        try:
            self.mqtt_client.connect(broker_ip)
            self.mqtt_client.subscribe(topic)
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.loop_start()
            print(f"🔌 [Protocol Translator] Listening to MQTT: {broker_ip} / {topic}")
        except Exception as e:
            print(f"❌ Failed to connect to MQTT broker: {e}")
        
    def _on_message(self, client, userdata, msg):
        """Automatically translates raw payload to your standard format"""
        try:
            raw_payload = msg.payload.decode()
            
            # Translate to your standard format
            standardized_data = {
                "sensor_id": msg.topic.split('/')[-1],
                "value": float(raw_payload),
                "timestamp": time.time(),
                "protocol": "MQTT"
            }
            
            # Send to your main pipeline
            self._process_sensor_data(standardized_data)
        except Exception as e:
            print(f"⚠️ Error parsing MQTT payload: {e}")

    def _process_sensor_data(self, data: dict):
        """
        Bridge to the main FastAPI pipeline.
        In a full deployment, this pushes to a message queue (Redis/Kafka) 
        or directly triggers the WebSocket broadcast.
        """
        print(f"📥 [Protocol Translator] Standardized Data: {data}")
        # TODO: Hook this into main.py's `manager.broadcast(data)`