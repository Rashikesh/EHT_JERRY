import logging
from datetime import datetime

logging.basicConfig(
    filename='safety_audit.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

def log_decision(sensor_data: dict, decision: dict):
    """Log every AI decision for audit trail"""
    log_entry = (
        f"Gas={sensor_data['gas']}% | "
        f"Pressure={sensor_data['pressure']} bar | "
        f"Temp={sensor_data['temperature']}°C | "
        f"PermitBlocked={not decision['permit_active']} | "
        f"Confidence={decision.get('confidence', 0)}% | "
        f"Reason={decision.get('blocked_reason', 'N/A')}"
    )
    
    if decision['permit_active']:
        logging.info(f"PERMIT ACTIVE | {log_entry}")
    else:
        logging.warning(f"PERMIT BLOCKED | Confidence: {decision['confidence']}% | {log_entry}")
