# backend/self_harnessing_ai.py
import numpy as np
from collections import deque

class SelfHarnessingAI:
    def __init__(self, learning_window=1000): # Observe last 1000 readings
        self.readings = deque(maxlen=learning_window)
        self.is_learning = True
        self.dynamic_threshold = None

    def observe(self, value: float):
        self.readings.append(value)
        
        # If we have enough data, calculate the dynamic baseline
        if len(self.readings) >= 100:
            mean = np.mean(self.readings)
            std_dev = np.std(self.readings)
            
            # Dynamic threshold: 3 Standard Deviations above normal
            self.dynamic_threshold = mean + (3 * std_dev)
            self.is_learning = False
            
    def evaluate_risk(self, current_value: float) -> dict:
        if self.is_learning:
            return {"status": "LEARNING", "message": f"AI is learning plant baseline ({len(self.readings)}/1000 readings)"}
        
        # Calculate how far it deviates from the learned normal
        deviation = (current_value - np.mean(self.readings)) / np.std(self.readings)
        
        if current_value > self.dynamic_threshold:
            return {
                "status": "CRITICAL", 
                "reason": f"Value {current_value} exceeds dynamic baseline by {deviation:.2f} sigma",
                "learned_baseline": round(self.dynamic_threshold, 2)
            }
        return {"status": "NORMAL", "learned_baseline": round(self.dynamic_threshold, 2)}