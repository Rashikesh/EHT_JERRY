import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.gas_readings = []
        self.mean = 0
        self.std = 0
    
    def check_anomaly(self, gas: float) -> tuple[bool, float, float]:
        """Returns (is_anomaly, mean, std)"""
        self.gas_readings.append(gas)
        
        # Need at least 10 readings to calculate stats
        if len(self.gas_readings) < 10:
            return False, 0, 0
        
        # Calculate mean and standard deviation
        self.mean = np.mean(self.gas_readings[-50:])  # Last 50 readings
        self.std = np.std(self.gas_readings[-50:])
        
        # If current reading is >3 standard deviations from mean = anomaly
        if abs(gas - self.mean) > 3 * self.std:
            return True, self.mean, self.std
        
        return False, self.mean, self.std
