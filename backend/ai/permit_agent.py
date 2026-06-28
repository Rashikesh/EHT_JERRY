# backend/ai/permit_agent.py
from ai.rag_engine import rag_engine
from ai.shift_analyzer import shift_analyzer

class PermitAgent:
    def __init__(self):
        # Single Sensor Thresholds (Absolute limits)
        self.gas_threshold = 40.0
        self.pressure_threshold = 2400.0
        self.temp_threshold = 65.0
        
        # Compound Risk Thresholds (Dangerous combinations)
        self.compound_gas_threshold = 15.0  # Lower limit if hot work is active

    def evaluate(self, sensor_data: dict, active_permits: list = None, 
                 cctv_alerts: list = None, ml_anomaly: dict = None,
                 shift_data: dict = None) -> dict:
        gas = sensor_data.get("gas", 0)
        pressure = sensor_data.get("pressure", 0)
        temp = sensor_data.get("temperature", 0)
        
        reasons = []
        is_compound_risk = False

        # 🆕 Calculate fatigue multiplier from shift data
        fatigue_multiplier = 1.0
        shift_risk_level = "low"
        if shift_data:
            shift_analysis = shift_analyzer.analyze_shift(shift_data)
            fatigue_multiplier = shift_analysis['fatigue_multiplier']
            shift_risk_level = shift_analysis['risk_level']
            
            # Adjust thresholds based on fatigue (lower = more sensitive)
            adjusted_gas_threshold = self.gas_threshold / fatigue_multiplier
            adjusted_pressure_threshold = self.pressure_threshold / fatigue_multiplier
            adjusted_temp_threshold = self.temp_threshold / fatigue_multiplier
        else:
            adjusted_gas_threshold = self.gas_threshold
            adjusted_pressure_threshold = self.pressure_threshold
            adjusted_temp_threshold = self.temp_threshold

        # 1. Check Single Sensor Absolute Limits (with fatigue adjustment)
        if gas > adjusted_gas_threshold:
            if fatigue_multiplier > 1.0:
                reasons.append(f"Gas levels critical ({gas}%) - Adjusted threshold: {adjusted_gas_threshold:.1f}% (Fatigue: {shift_risk_level})")
            else:
                reasons.append(f"Gas levels critical ({gas}%)")
                
        if pressure > adjusted_pressure_threshold:
            if fatigue_multiplier > 1.0:
                reasons.append(f"Pressure exceeding limits ({pressure} bar) - Adjusted threshold: {adjusted_pressure_threshold:.0f} bar (Fatigue: {shift_risk_level})")
            else:
                reasons.append(f"Pressure exceeding limits ({pressure} bar)")
                
        if temp > adjusted_temp_threshold:
            if fatigue_multiplier > 1.0:
                reasons.append(f"Temperature dangerously high ({temp}°C) - Adjusted threshold: {adjusted_temp_threshold:.1f}°C (Fatigue: {shift_risk_level})")
            else:
                reasons.append(f"Temperature dangerously high ({temp}°C)")

        # 2. Check Compound Risks (The "AI Predictive Layer")
        if active_permits:
            if "hot_work" in active_permits and gas > self.compound_gas_threshold:
                reasons.append(f"COMPOUND RISK: Hot Work active while gas is {gas}% (Threshold: {self.compound_gas_threshold}%)")
                is_compound_risk = True
                
            if "confined_space" in active_permits and (gas > 5 or temp > 40):
                reasons.append(f"COMPOUND RISK: Confined space entry unsafe due to gas/temp")
                is_compound_risk = True

        # 3. Check CCTV AI Feeds (Simulated)
        if cctv_alerts:
            if "smoke_detected" in cctv_alerts:
                reasons.append("CCTV AI: Smoke detected in Zone B")
                is_compound_risk = True
            if "ppe_violation" in cctv_alerts and gas > 10:
                reasons.append("COMPOUND RISK: CCTV detected missing PPE in gas zone")
                is_compound_risk = True

        # 4. Check ML Anomaly Detection
        if ml_anomaly and ml_anomaly.get('is_anomaly'):
            reasons.append(f"ML ANOMALY: Statistical anomaly detected (score: {ml_anomaly.get('anomaly_score', 0)})")
            is_compound_risk = True

        permit_active = len(reasons) == 0
        
        ai_justification = ""
        if not permit_active:
            query = f"Gas {gas}%, Pressure {pressure} bar, Temp {temp}°C. Reasons: {', '.join(reasons)}"
            rag_context = rag_engine.get_context(query)
            
            prefix = "🧠 COMPOUND RISK DETECTED: " if is_compound_risk else "⚠️ AI SAFETY ALERT: "
            ai_justification = f"{prefix}Permit BLOCKED.\n\nReasons:\n- " + "\n- ".join(reasons)
            
            if fatigue_multiplier > 1.0:
                ai_justification += f"\n\n🌙 SHIFT FATIGUE FACTOR: {fatigue_multiplier}x (Risk Level: {shift_risk_level})"
                ai_justification += f"\n   Safety thresholds automatically lowered for worker protection."
            
            ai_justification += f"\n\n{rag_context}"

        return {
            "permit_active": permit_active,
            "blocked_reason": reasons[0] if reasons else None,
            "ai_justification": ai_justification,
            "is_compound_risk": is_compound_risk,
            "confidence": 99 if is_compound_risk else 95,
            "fatigue_multiplier": fatigue_multiplier,
            "shift_risk_level": shift_risk_level
        }

permit_agent = PermitAgent()