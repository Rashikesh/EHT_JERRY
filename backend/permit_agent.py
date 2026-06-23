from rag_engine import rag_engine

class PermitAgent:
    def __init__(self):
        self.is_permit_active = True
        self.last_alert = ""

    def evaluate_conditions(self, sensor_data: dict) -> dict:
        gas = sensor_data.get("gas", 0)
        pressure = sensor_data.get("pressure", 0)
        temp = sensor_data.get("temperature", 0)

        # Calculate confidence based on how far above threshold
        confidence = 0
        reasons = []
        
        if gas > 40:
            confidence += min(50, (gas - 40) * 2)  # More gas = more confident
            reasons.append(f"Gas at {gas}% (threshold: 40%)")
        
        if pressure > 2400:
            confidence += min(30, (pressure - 2400) / 20)
            reasons.append(f"Pressure at {pressure} bar (threshold: 2400)")
        
        if temp > 65:
            confidence += min(20, (temp - 65) * 1.5)
            reasons.append(f"Temperature at {temp}°C (threshold: 65)")
        
        is_dangerous = confidence > 0
        
        if is_dangerous:
            self.is_permit_active = False
            self.last_alert = rag_engine.get_safety_justification(sensor_data)
        else:
            self.is_permit_active = True
            self.last_alert = "Environmental parameters are within safe limits."

        return {
            "permit_active": self.is_permit_active,
            "ai_justification": self.last_alert,
            "blocked_reason": reasons[0] if reasons else None,
            "confidence": min(100, int(confidence)),  # 0-100%
            "all_reasons": reasons
        }

permit_agent = PermitAgent()
