# backend/ai/compound_risk_engine.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any

@dataclass
class TemporalEvent:
    event_type: str      # "gas_reading", "permit_issued", "shift_change"
    timestamp: datetime
    zone: str
    payload: dict        # {gas_level: 35.0, permit_type: "confined_space", ...}

@dataclass  
class CompoundRiskRule:
    name: str
    description: str
    regulatory_reference: str
    conditions: List[dict]
    action: str

# The Visakhapatnam Rule
CONFINED_SPACE_GAS_RULE = CompoundRiskRule(
    name="confined_space_gas_risk",
    description="Confined space entry during rising gas levels",
    regulatory_reference="OISD-Std-164-Section-4.2",
    conditions=[
        {"event": "permit_issued", "permit_type": "confined_space", "within_seconds": 1800},
        {"event": "gas_reading", "gas_level_min": 15.0, "trend": "rising", "within_seconds": 600},
    ],
    action="BLOCK_PERMIT"
)

class CompoundRiskEngine:
    def __init__(self):
        self.event_history: List[TemporalEvent] = []
        self.active_rules = [CONFINED_SPACE_GAS_RULE]
        self.triggered_alerts = []
        self.timeline_events = [] # For frontend visualization

    def ingest_event(self, event: TemporalEvent):
        self.event_history.append(event)
        # Keep last 50 events
        if len(self.event_history) > 50:
            self.event_history = self.event_history[-50:]
        
        # Check rules
        for rule in self.active_rules:
            if self._check_rule(rule, event):
                self._trigger_alert(rule, event)

    def _check_rule(self, rule: CompoundRiskRule, current_event: TemporalEvent) -> bool:
        # Simplified check for the demo: look for matching events in the history
        for condition in rule.conditions:
            event_type = condition["event"]
            within_seconds = condition.get("within_seconds", 3600)
            cutoff = current_event.timestamp - timedelta(seconds=within_seconds)
            
            # Find matching event in history
            found = False
            for hist_event in self.event_history:
                if hist_event.timestamp < cutoff:
                    continue
                if hist_event.event_type == event_type:
                    # Check specific conditions
                    if event_type == "permit_issued":
                        if hist_event.payload.get("permit_type") == condition.get("permit_type"):
                            found = True
                            break
                    elif event_type == "gas_reading":
                        if hist_event.payload.get("gas_level", 0) >= condition.get("gas_level_min", 0):
                            found = True
                            break
            if not found:
                return False
        return True

    def _trigger_alert(self, rule: CompoundRiskRule, event: TemporalEvent):
        alert = {
            "rule_name": rule.name,
            "action": rule.action,
            "citation": rule.regulatory_reference,
            "timestamp": event.timestamp.isoformat(),
            "reason": rule.description
        }
        # Prevent duplicate alerts for the same rule in short succession
        if not self.triggered_alerts or self.triggered_alerts[-1]["rule_name"] != rule.name:
            self.triggered_alerts.append(alert)
            self.timeline_events.append({
                "time": event.timestamp.strftime("%H:%M:%S"),
                "event": f" SYSTEM BLOCK: {rule.action}",
                "detail": f"Citing {rule.regulatory_reference}",
                "type": "BLOCK"
            })

    def get_state(self):
        return {
            "alerts": self.triggered_alerts[-3:],
            "timeline": self.timeline_events[-10:]
        }

compound_risk_engine = CompoundRiskEngine()