# backend/ai/predictive_analyzer.py
import numpy as np
from collections import deque
import threading

class PredictiveAnalyzer:
    """Predicts threshold breaches before they happen"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.gas_history = deque(maxlen=30)
        self.pressure_history = deque(maxlen=30)
        self.temp_history = deque(maxlen=30)
        
        print("🔮 Predictive Analyzer (Singleton) initialized")
    
    def add_reading(self, gas: float, pressure: float, temp: float):
        """Add new reading to history"""
        self.gas_history.append(gas)
        self.pressure_history.append(pressure)
        self.temp_history.append(temp)
    
    def predict_breach(self) -> dict:
        """Predict if/when threshold will be breached"""
        if len(self.gas_history) < 10:
            return {'predictions': [], 'trends': {'gas': 0, 'pressure': 0, 'temperature': 0}}
        
        predictions = []
        
        # Calculate trends
        gas_trend = np.polyfit(range(len(self.gas_history)), list(self.gas_history), 1)[0]
        pressure_trend = np.polyfit(range(len(self.pressure_history)), list(self.pressure_history), 1)[0]
        temp_trend = np.polyfit(range(len(self.temp_history)), list(self.temp_history), 1)[0]
        
        current_gas = self.gas_history[-1]
        current_pressure = self.pressure_history[-1]
        current_temp = self.temp_history[-1]
        
        # Predict gas breach
        if gas_trend > 0 and current_gas < 40:
            gas_to_breach = (40 - current_gas) / gas_trend * 2
            if gas_to_breach < 30 and gas_to_breach > 0:
                predictions.append({
                    'type': 'gas_breach',
                    'current': round(current_gas, 1),
                    'threshold': 40,
                    'trend': round(gas_trend, 3),
                    'minutes_to_breach': round(gas_to_breach, 1),
                    'severity': 'critical' if gas_to_breach < 10 else 'warning'
                })
        
        # Predict pressure breach
        if pressure_trend > 0 and current_pressure < 2400:
            pressure_to_breach = (2400 - current_pressure) / pressure_trend * 2
            if pressure_to_breach < 30 and pressure_to_breach > 0:
                predictions.append({
                    'type': 'pressure_breach',
                    'current': round(current_pressure, 1),
                    'threshold': 2400,
                    'trend': round(pressure_trend, 3),
                    'minutes_to_breach': round(pressure_to_breach, 1),
                    'severity': 'critical' if pressure_to_breach < 10 else 'warning'
                })
        
        return {
            'predictions': predictions,
            'trends': {
                'gas': round(gas_trend, 3),
                'pressure': round(pressure_trend, 3),
                'temperature': round(temp_trend, 3)
            }
        }

predictive_analyzer = PredictiveAnalyzer()