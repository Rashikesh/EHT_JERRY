# backend/mqtt_manager.py
import paho.mqtt.client as mqtt
import json
import threading
from typing import Callable, Dict

class MQTTManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        self.client = mqtt.Client()
        self.subscribers: Dict[str, list] = {}
        self._connected = False
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self._connected = True
                print("✅ MQTT Manager connected to broker")
            else:
                print(f"❌ MQTT connection failed with code {rc}")
        
        def on_message(client, userdata, msg):
            # Route message to all registered subscribers
            topic = msg.topic
            if topic in self.subscribers:
                payload = json.loads(msg.payload.decode())
                for callback in self.subscribers[topic]:
                    callback(payload)
        
        self.client.on_connect = on_connect
        self.client.on_message = on_message
    
    def connect(self, host: str = "localhost", port: int = 1883):
        """Connect to MQTT broker"""
        try:
            self.client.connect(host, port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ MQTT connection error: {e}")
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic and register callback"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
            self.client.subscribe(topic)
        self.subscribers[topic].append(callback)
    
    def publish(self, topic: str, data: dict):
        """Publish message to topic"""
        self.client.publish(topic, json.dumps(data))
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()

# Global singleton instance
mqtt_manager = MQTTManager()