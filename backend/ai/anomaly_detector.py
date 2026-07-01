import threading
import numpy as np
from collections import deque

class AnomalyDetector:
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
        
        # 🚀 LAZY LOADING: Don't load sklearn yet!
        self.model = None 
        self.baseline_readings = deque(maxlen=150)
        self.is_trained = False
        self.learning_mode = True
        print("🤖 Anomaly Detector initialized (Lazy Mode - saving memory).")

    def _load_model(self):
        """Only import and create the model when we actually need it"""
        if self.model is None:
            print("⏳ Loading Isolation Forest into memory...")
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
            print("✅ Isolation Forest loaded.")
    
    def add_reading(self, gas: float, pressure: float, temp: float):
        if self.learning_mode:
            self.baseline_readings.append([gas, pressure, temp])
            if len(self.baseline_readings) >= 150 and not self.is_trained:
                self._train_model()
    
    def _train_model(self):
        try:
            self._load_model() # Ensure model is loaded before training
            data = np.array(list(self.baseline_readings))
            self.model.fit(data)
            self.is_trained = True
            self.learning_mode = False
            print(f"✅ Isolation Forest trained on {len(self.baseline_readings)} baseline samples")
        except Exception as e:
            print(f"❌ Error training model: {e}")
    
    def detect_anomaly(self, gas: float, pressure: float, temp: float) -> dict:
        if not self.is_trained:
            self.add_reading(gas, pressure, temp)
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0,
                'status': 'learning'
            }
        
        try:
            self._load_model() # Ensure model is loaded
            reading = np.array([[gas, pressure, temp]])
            prediction = self.model.predict(reading)[0]
            score = self.model.decision_function(reading)[0]
            confidence = int((score + 1) * 50)
            confidence = max(0, min(100, confidence))
            
            return {
                'is_anomaly': prediction == -1,
                'anomaly_score': round(score, 3),
                'confidence': confidence,
                'status': 'active'
            }
        except Exception as e:
            print(f"❌ Anomaly detection error: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0,
                'status': 'error'
            }

anomaly_detector = AnomalyDetector()