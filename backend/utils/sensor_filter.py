from collections import deque

class SensorFilter:
    def __init__(self, window_size=5):
        self.gas_history = deque(maxlen=window_size)
        self.pressure_history = deque(maxlen=window_size)
        self.temp_history = deque(maxlen=window_size)
    
    def filter_reading(self, gas: float, pressure: float, temp: float) -> dict:
        """Returns smoothed values"""
        self.gas_history.append(gas)
        self.pressure_history.append(pressure)
        self.temp_history.append(temp)
        
        return {
            'gas_smooth': sum(self.gas_history) / len(self.gas_history),
            'pressure_smooth': sum(self.pressure_history) / len(self.pressure_history),
            'temp_smooth': sum(self.temp_history) / len(self.temp_history),
            'gas_raw': gas,
            'pressure_raw': pressure,
            'temp_raw': temp
        }
