# backend/ai/shift_analyzer.py
from datetime import datetime
import threading

class ShiftAnalyzer:
    """Analyzes shift data for fatigue risk"""
    
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
        
        self.shift_risks = {
            'night': 1.5,
            'early_morning': 1.2,
            'overtime': 1.8,
            'regular': 1.0
        }
        print("🌙 Shift Analyzer (Singleton) initialized")
    
    def analyze_shift(self, shift_data: dict) -> dict:
        """Calculate fatigue risk multiplier"""
        current_hour = datetime.now().hour
        shift_type = shift_data.get('type', 'regular')
        hours_worked = shift_data.get('hours_worked', 8)
        
        # Time-based risk
        if 22 <= current_hour or current_hour < 6:
            time_risk = self.shift_risks['night']
        elif 4 <= current_hour < 6:
            time_risk = self.shift_risks['early_morning']
        else:
            time_risk = self.shift_risks['regular']
        
        # Overtime risk
        if hours_worked > 10:
            overtime_risk = self.shift_risks['overtime']
        else:
            overtime_risk = 1.0
        
        fatigue_multiplier = max(time_risk, overtime_risk)
        
        return {
            'fatigue_multiplier': fatigue_multiplier,
            'risk_level': 'high' if fatigue_multiplier > 1.3 else 'medium' if fatigue_multiplier > 1.1 else 'low',
            'factors': {
                'night_shift': time_risk > 1.0,
                'overtime': overtime_risk > 1.0,
                'hours_worked': hours_worked
            }
        }

shift_analyzer = ShiftAnalyzer()