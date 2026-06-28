# backend/ai/cctv_simulator.py
import random
import time

class CCTVSimulator:
    """Simulates realistic CCTV alerts for demo"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.alert_probability = 0.05
        self.last_alert_time = 0
        self.alert_cooldown = 30
        print("📷 CCTV Simulator (Singleton) initialized")
    
    def check_for_alerts(self) -> list:
        """Simulate CCTV analysis"""
        current_time = time.time()
        
        if current_time - self.last_alert_time < self.alert_cooldown:
            return []
        
        alerts = []
        
        if random.random() < self.alert_probability:
            alerts.append({
                'type': 'ppe_violation',
                'description': 'Worker detected without hard hat in Zone B',
                'severity': 'warning',
                'confidence': round(random.uniform(0.85, 0.98), 2),
                'location': 'Zone B - Welding Area'
            })
            self.last_alert_time = current_time
        
        if random.random() < self.alert_probability * 0.3:
            alerts.append({
                'type': 'smoke_detected',
                'description': 'Smoke detected near storage tanks',
                'severity': 'critical',
                'confidence': round(random.uniform(0.90, 0.99), 2),
                'location': 'Zone C - Storage Area'
            })
            self.last_alert_time = current_time
        
        return alerts

cctv_simulator = CCTVSimulator()