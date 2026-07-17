# backend/ai/compound_risk_engine.py
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Tuple

class SafetyKnowledgeGraph:
    """A lightweight, in-memory Knowledge Graph for Equipment-Permit-Risk relationships."""
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Tuple[str, str, str]] = [] # (source, target, relation)

    def add_node(self, node_id: str, node_type: str, **properties):
        self.nodes[node_id] = {"type": node_type, **properties}

    def add_edge(self, source: str, target: str, relation: str):
        self.edges.append((source, target, relation))

    def get_permits_in_zone(self, zone_id: str) -> List[Dict]:
        """Query: Find all active permits located in a specific zone."""
        permits = []
        for source, target, relation in self.edges:
            if target == zone_id and relation == "LOCATED_IN":
                node_data = self.nodes.get(source, {})
                if node_data.get("type") == "Permit" and node_data.get("status") == "active":
                    permits.append(node_data)
        return permits

# Initialize the Graph
kg = SafetyKnowledgeGraph()
kg.add_node("Zone_A", "Zone", location="Boiler Room")
kg.add_node("Valve_1", "Equipment", zone="Zone_A", maintenance_overdue=True)
kg.add_node("Permit_HW_01", "Permit", type="hot_work", zone="Zone_A", status="active")
kg.add_edge("Permit_HW_01", "Zone_A", "LOCATED_IN")
kg.add_edge("Valve_1", "Zone_A", "LOCATED_IN")


class CompoundRiskEngine:
    def __init__(self):
        # Async-safe lock
        self._lock = asyncio.Lock()
        
        # State
        self.sensor_state = {"gas": 0.0, "pressure": 0.0, "temp": 0.0, "trend_gas_per_min": 0.0}
        self.history_gas: List[Tuple[datetime, float]] = []
        
        # Simulated external states (In production, these come from APIs)
        self.permit_state = {"active": False, "type": "none", "zone": "none"}
        self.shift_state = {"is_night_shift": False, "hours_worked": 8}
        self.maintenance_state = {"is_overdue": False}
        
        self.graph = kg
        print("🧠 Async-Safe Compound Risk Engine & Knowledge Graph initialized.")

    async def update_sensors(self, gas: float, pressure: float, temp: float):
        """Thread-safe sensor update with timestamped history."""
        async with self._lock:
            now = datetime.now()
            self.history_gas.append((now, gas))
            
            # Keep only last 10 readings (approx 20 seconds at 2s intervals)
            if len(self.history_gas) > 10:
                self.history_gas.pop(0)
            
            # Time-weighted trend calculation (Fixes the uniform interval bug)
            if len(self.history_gas) >= 2:
                dt_seconds = (self.history_gas[-1][0] - self.history_gas[0][0]).total_seconds()
                if dt_seconds > 0:
                    gas_change = self.history_gas[-1][1] - self.history_gas[0][1]
                    self.sensor_state["trend_gas_per_min"] = (gas_change / dt_seconds) * 60
                else:
                    self.sensor_state["trend_gas_per_min"] = 0.0
            
            self.sensor_state.update({"gas": gas, "pressure": pressure, "temp": temp})

    async def update_context(self, permit_active: bool, permit_type: str, zone: str, is_night: bool, hours: int, maint_overdue: bool):
        """Update external context states."""
        async with self._lock:
            self.permit_state = {"active": permit_active, "type": permit_type, "zone": zone}
            self.shift_state = {"is_night_shift": is_night, "hours_worked": hours}
            self.maintenance_state = {"is_overdue": maint_overdue}
            
            # Update Knowledge Graph dynamically
            if permit_active:
                self.graph.nodes["Permit_HW_01"]["status"] = "active"
                self.graph.nodes["Permit_HW_01"]["type"] = permit_type
            else:
                self.graph.nodes["Permit_HW_01"]["status"] = "inactive"

    async def evaluate(self) -> Dict[str, Any]:
        """Evaluate compound risks using the Knowledge Graph and multi-agent logic."""
        async with self._lock:
            gas = self.sensor_state["gas"]
            trend = self.sensor_state["trend_gas_per_min"]
            
            score = 0.0
            reasons = []
            actions = []
            
            # 1. Query the Knowledge Graph for Permit Conflicts
            active_permits = self.graph.get_permits_in_zone("Zone_A")
            
            # 2. Predictive Forecasting (Guarded against div/zero and negative trends)
            predicted_gas_30m = gas + (trend * 30)
            if trend > 0.1 and predicted_gas_30m > 35.0:
                score += 0.3
                reasons.append(f"Predictive trend indicates gas reaching {predicted_gas_30m:.1f}% in 30 minutes.")
                actions.append("Initiate preemptive ventilation.")

            # 3. Compound Risk: Hot Work + Elevated Gas (Graph + Sensor)
            if active_permits and active_permits[0].get("type") == "hot_work" and gas > 15.0:
                score += 0.4
                reasons.append(f"Knowledge Graph conflict: Active Hot Work permit in Zone A with elevated gas ({gas}%).")
                actions.append("Revoke hot work permit immediately.")

            # 4. Human Factor: Fatigue + Danger
            if self.shift_state["is_night_shift"] and self.shift_state["hours_worked"] > 10 and gas > 20.0:
                score += 0.2
                reasons.append("Night shift fatigue (>10h) compounds risk during elevated gas levels.")
                actions.append("Alert shift supervisor.")

            # 5. Equipment Vulnerability (Graph + Sensor)
            valve_data = self.graph.nodes.get("Valve_1", {})
            if valve_data.get("maintenance_overdue") and (self.sensor_state["pressure"] > 2000 or gas > 25.0):
                score += 0.3
                reasons.append("Equipment (Valve_1) is overdue for maintenance and currently under stress.")
                actions.append("Flag equipment for immediate inspection.")

            score = min(1.0, score)
            is_critical = score >= 0.6 or gas >= 40.0

            # Structured RAG Query (Clean keywords for FAISS, no emojis)
            rag_keywords = []
            if "Hot Work" in str(active_permits): rag_keywords.append("hot work permit")
            if gas > 15: rag_keywords.append("elevated gas levels")
            if trend > 0.1: rag_keywords.append("rising gas trend")
            rag_query = " ".join(rag_keywords) if rag_keywords else "general industrial safety compliance"

            # Safe prediction math
            if trend > 0.1:
                mins_to_breach = max(0, int((40.0 - gas) / trend))
            else:
                mins_to_breach = 999

            return {
                "score": round(score, 2),
                "is_critical": is_critical,
                "reasons": reasons,
                "actions": actions,
                "rag_query": rag_query,
                "mins_to_breach": mins_to_breach
            }

# Module-level instance (Safe for FastAPI lifespan)
compound_risk_engine = CompoundRiskEngine()