# backend/permit_agent.py
"""
Permit Agent: Evaluates sensor data against safety thresholds and 
generates AI justifications using the RAG Engine.
"""
from rag_engine import rag_engine

class PermitAgent:
    def __init__(self):
        # Safety Thresholds
        self.gas_threshold = 40.0
        self.pressure_threshold = 2400.0
        self.temp_threshold = 65.0

    def evaluate(self, sensor_data: dict) -> dict:
        gas = sensor_data.get("gas", 0)
        pressure = sensor_data.get("pressure", 0)
        temp = sensor_data.get("temperature", 0)

        reasons = []
        if gas > self.gas_threshold:
            reasons.append(f"Gas levels critical ({gas}%)")
        if pressure > self.pressure_threshold:
            reasons.append(f"Pressure exceeding limits ({pressure} bar)")
        if temp > self.temp_threshold:
            reasons.append(f"Temperature dangerously high ({temp}°C)")

        permit_active = len(reasons) == 0
        
        ai_justification = ""
        if not permit_active:
            # 🧠 ONLY query the RAG engine if the permit is blocked (saves compute)
            query = f"Gas {gas}%, Pressure {pressure} bar, Temperature {temp}°C. Reasons: {', '.join(reasons)}"
            rag_context = rag_engine.get_context(query)
            
            ai_justification = (
                f"⚠️ AI SAFETY ALERT: Permit BLOCKED.\n\n"
                f"Reasons:\n- " + "\n- ".join(reasons) + 
                f"\n\n{rag_context}"
            )

        return {
            "permit_active": permit_active,
            "blocked_reason": reasons[0] if reasons else None,
            "ai_justification": ai_justification,
            "confidence": 95 if not permit_active else 100
        }

# Global instance
permit_agent = PermitAgent()