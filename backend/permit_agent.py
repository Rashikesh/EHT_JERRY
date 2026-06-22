from rag_engine import rag_engine

class PermitAgent:
    def __init__(self):
        self.is_permit_active = True
        self.last_alert = ""

    def evaluate_conditions(self, sensor_data: dict) -> dict:
        gas = sensor_data.get("gas", 0)
        pressure = sensor_data.get("pressure", 0)
        temp = sensor_data.get("temperature", 0)

        is_dangerous = (gas > 40) or (pressure > 2400) or (temp > 65)

        if is_dangerous:
            self.is_permit_active = False
            self.last_alert = rag_engine.get_safety_justification(sensor_data)
        else:
            self.is_permit_active = True
            self.last_alert = "Environmental parameters are within safe limits."

        return {
            "permit_active": self.is_permit_active,
            "ai_justification": self.last_alert,
            "blocked_reason": "Gas > 40%" if gas > 40 else ("Pressure > 2400" if pressure > 2400 else "Temp > 65°C") if is_dangerous else None
        }

permit_agent = PermitAgent()
