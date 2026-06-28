# backend/ai/incident_matcher.py
import threading

class IncidentMatcher:
    """Matches current conditions to historical incidents"""
    
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
        
        self.incidents = [
            {
                'id': 'INC-2024-001',
                'date': '2024-03-15',
                'gas_level': 45,
                'pressure': 2600,
                'temp': 68,
                'cause': 'Hot work near gas leak',
                'outcome': 'Minor flash fire, no injuries',
                'lessons': 'Increased gas threshold for hot work areas'
            },
            {
                'id': 'INC-2024-002',
                'date': '2024-05-22',
                'gas_level': 38,
                'pressure': 2450,
                'temp': 62,
                'cause': 'Night shift fatigue - delayed response',
                'outcome': 'Equipment damage, evacuation',
                'lessons': 'Lower thresholds during night shifts'
            },
            {
                'id': 'INC-2024-003',
                'date': '2024-07-10',
                'gas_level': 52,
                'pressure': 2700,
                'temp': 70,
                'cause': 'CCTV detected smoke before sensors',
                'outcome': 'Early intervention prevented major incident',
                'lessons': 'CCTV integration critical for early detection'
            }
        ]
        print("📚 Incident Matcher (Singleton) initialized")
    
    def find_similar_incidents(self, current_conditions: dict) -> list:
        """Find historical incidents similar to current conditions"""
        gas = current_conditions.get('gas', 0)
        pressure = current_conditions.get('pressure', 0)
        temp = current_conditions.get('temperature', 0)
        
        similar = []
        
        for incident in self.incidents:
            gas_sim = max(0, 100 - abs(gas - incident['gas_level']) * 2)
            pressure_sim = max(0, 100 - abs(pressure - incident['pressure']) * 0.1)
            temp_sim = max(0, 100 - abs(temp - incident['temp']) * 2)
            
            similarity = (gas_sim + pressure_sim + temp_sim) / 3
            
            if similarity > 60:
                similar.append({
                    **incident,
                    'similarity_score': round(similarity, 1)
                })
        
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar[:3]

# ✅ THIS LINE WAS MISSING - Creates the global singleton instance
incident_matcher = IncidentMatcher()