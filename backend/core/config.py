# backend/config.py
import os
from typing import Optional

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        # Load from environment variables or defaults
        self.mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.ws_url = os.getenv("WS_URL", "ws://localhost:8000/ws")
        self.gas_threshold = float(os.getenv("GAS_THRESHOLD", "40.0"))
        self.pressure_threshold = float(os.getenv("PRESSURE_THRESHOLD", "2400.0"))
        self.temp_threshold = float(os.getenv("TEMP_THRESHOLD", "65.0"))
        self.enable_rag = os.getenv("ENABLE_RAG", "true").lower() == "true"
        self.pdf_path = os.getenv("OSHA_PDF_PATH", "osha_h2s.pdf")
    
    def get(self, key: str) -> Optional[str]:
        return getattr(self, key, None)
    
    def set(self, key: str, value):
        setattr(self, key, value)

# Global singleton
config = ConfigManager()