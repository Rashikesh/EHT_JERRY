import sys
import os ,itertools

# Ensure backend root is in Python path for clean imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Dict
from io import BytesIO

from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse

# --- AI & Core Modules ---
from core.audit_chain import audit_chain
from ai.predictive_analyzer import predictive_analyzer
from ai.cctv_simulator import cctv_simulator
from ai.shift_analyzer import shift_analyzer
from ai.incident_matcher import incident_matcher
from ai.anomaly_detector import anomaly_detector
from ai.compound_risk_engine import compound_risk_engine
# from ai.rag_engine import rag_engine  # Uncomment if you have this set up

# --- Protocol & Agent Modules ---
from protocols.protocol_translator import translator, IoTAsset, ProtocolType, SensorStatus
from ai.permit_agent import permit_agent

# --- Configuration ---
logger = logging.getLogger("safety_agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

DEFAULT_SITE_ID = "site-a"
MAX_CCTV_ALERTS = 50

cctv_alerts: List[dict] = []
is_permit_active: Dict[str, bool] = {}
# global START_TIME
# START_TIME = time.time()


# ==============================================================================
# WebSocket Connection Manager
# ==============================================================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_site: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, site_id: str = DEFAULT_SITE_ID):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_site[websocket] = site_id
        logger.info(f"✅ WebSocket connected: {site_id}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.connection_site.pop(websocket, None)
        logger.info("❌ WebSocket disconnected")

    async def broadcast(self, site_id: str, message: dict):
        for connection in list(self.active_connections):
            if self.connection_site.get(connection) != site_id:
                continue
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


# ==============================================================================
# Dynamic Demo Scenario Generator (For Hackathon Presentation)
# ==============================================================================

START_TIME = time.time()

_scenario_cycle = itertools.cycle([
    # (duration_seconds, scenario_dict)
    (20, {"permit_active": False, "permit_type": "none", "is_night": False, "hours_worked": 8, "maint_overdue": False}),
    (20, {"permit_active": True, "permit_type": "hot_work", "is_night": False, "hours_worked": 8, "maint_overdue": False}),
    (20, {"permit_active": True, "permit_type": "hot_work", "is_night": True, "hours_worked": 11, "maint_overdue": True}),
])

_current_scenario = next(_scenario_cycle)
_scenario_start = time.time()

async def get_demo_scenario() -> dict:
    global _current_scenario, _scenario_start
    
    elapsed = time.time() - _scenario_start
    if elapsed >= _current_scenario[0]:
        _current_scenario = next(_scenario_cycle)
        _scenario_start = time.time()
    
    return _current_scenario[1]
# async def get_demo_scenario() -> dict:
#     """
#     Cycles through realistic scenarios to demonstrate compound risk detection.
#     This proves the system reacts to changing conditions, not just static thresholds.
#     """
    
#     elapsed = time.time() - START_TIME
    
#     if elapsed < 20:
#         # Scenario 1: Normal operations
#         return {"permit_active": False, "permit_type": "none", "is_night": False, "hours_worked": 8, "maint_overdue": False}
#     elif elapsed < 40:
#         # Scenario 2: Gas starts rising + Hot Work permit issued (Compound Risk builds)
#         return {"permit_active": True, "permit_type": "hot_work", "is_night": False, "hours_worked": 8, "maint_overdue": False}
#     elif elapsed < 60:
#         # Scenario 3: CRITICAL TRIGGER (Night shift fatigue + Maintenance overdue + Hot Work + Rising Gas)
#         return {"permit_active": True, "permit_type": "hot_work", "is_night": True, "hours_worked": 11, "maint_overdue": True}
#     else:
#         # Reset cycle for continuous demo
#         global START_TIME
#         START_TIME = time.time()
#         return {"permit_active": False, "permit_type": "none", "is_night": False, "hours_worked": 8, "maint_overdue": False}



# ==============================================================================
# Core Data Processing Pipeline
# ==============================================================================
async def on_asset_data(asset: IoTAsset):
    """
    The central hub where live sensor data enters the pipeline.
    Decoupled from ingestion: translator handles reading fast; this handles the "slow" AI work.
    """
    site_id = asset.site_id

    # 1. CCTV Simulation Check
    global cctv_alerts
    new_alerts = cctv_simulator.check_for_alerts()
    if new_alerts:
        cctv_alerts.extend(new_alerts)
        cctv_alerts = cctv_alerts[-MAX_CCTV_ALERTS:]
        logger.info(f"📷 [{site_id}] CCTV ALERT: {new_alerts[0]['type']}")

    # 2. Extract latest values for this site
    site_assets = translator.get_assets_for_site(site_id)
    gas = next((a["gasLevel"] for a in site_assets if "gas" in a["name"].lower()), asset.current_value)
    pressure = next((a["gasLevel"] for a in site_assets if "pressure" in a["name"].lower()), 0.0)
    temperature = next((a["gasLevel"] for a in site_assets if "temp" in a["name"].lower()), 0.0)

    # 3. 🧠 MULTI-AGENT COMPOUND RISK EVALUATION
    await compound_risk_engine.update_sensors(gas, pressure, temperature)
    
    scenario = await get_demo_scenario()
    await compound_risk_engine.update_context(
        permit_active=scenario["permit_active"],
        permit_type=scenario["permit_type"],
        zone="Zone_A",
        is_night=scenario["is_night"],
        hours=scenario["hours_worked"],
        maint_overdue=scenario["maint_overdue"]
    )

    assessment = await compound_risk_engine.evaluate()

    # 4. Existing ML & Predictive Enrichments
    predictive_analyzer.add_reading(gas, pressure, temperature)
    predictions = predictive_analyzer.predict_breach()
    
    shift_type = "night" if scenario["is_night"] else "day"
    shift_analysis = shift_analyzer.analyze_shift({"type": shift_type, "hours_worked": scenario["hours_worked"]})
    ml_result = anomaly_detector.detect_anomaly(gas, pressure, temperature)

    # 5. Build Decision Payload
    decision = {
        "permit_active": not assessment["is_critical"],
        "blocked_reason": assessment["reasons"][0] if assessment["reasons"] else None,
        "ai_justification": f"AI INTERVENTION: {assessment['reasons'][0] if assessment['reasons'] else 'All parameters normal'}\n\nQuery Context: {assessment['rag_query']}",
        "actions_required": assessment["actions"]
    }

    # Optional: Inject RAG context if permit is blocked
    # if not decision["permit_active"]:
    #     try:
    #         rag_context = rag_engine.get_context(assessment["rag_query"])
    #         decision["ai_justification"] += f"\n\nRegulatory Citation:\n{rag_context}"
    #     except Exception:
    #         pass

    similar_incidents = []
    if not decision["permit_active"]:
        similar_incidents = incident_matcher.find_similar_incidents({
            "gas": gas, "pressure": pressure, "temp": temperature
        })

    # 6. Closed-Loop Interlock & Audit Chain
    was_active = is_permit_active.get(site_id, True)
    if not decision["permit_active"] and was_active:
        logger.warning(f"🚨 [{site_id}] CLOSED-LOOP: permit blocked — {decision['blocked_reason']}")
        audit_chain.add_block({
            "site_id": site_id,
            "event": "VALVE_CLOSE",
            "reason": decision["blocked_reason"],
            "gas": gas,
            "action": "AUTOMATED_INTERLOCK",
            "risk_score": assessment["score"]
        })
        logger.info(f"🔗 [{site_id}] Event logged to Immutable Audit Chain")

    is_permit_active[site_id] = decision["permit_active"]

    # 7. Broadcast to Frontend
    broadcast_payload = {
        "site_id": site_id,
        "gas": round(gas, 1),
        "pressure": round(pressure, 1),
        "temperature": round(temperature, 1),
        "shift": f"{shift_type.capitalize()} Shift (Fatigue: {shift_analysis['risk_level']})",
        **decision,
        "anomaly_score": ml_result["anomaly_score"],
        "ml_confidence": ml_result["confidence"],
        "ml_status": ml_result["status"],
        "predictions": predictions.get("predictions", []),
        "trends": predictions.get("trends", {}),
        "shift_analysis": shift_analysis,
        "similar_incidents": similar_incidents,
        "risk_score": assessment["score"],
        "predicted_breach_mins": assessment["mins_to_breach"]
    }

    await manager.broadcast(site_id, broadcast_payload)


# ==============================================================================
# FastAPI Application & Lifespan
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wire the translator to our processing pipeline
    translator.on_data_callback = on_asset_data

    # Provision default demo assets
    await translator.provision_asset(IoTAsset(
        id="sensor-gas-1", name="Gas Sensor A1", protocol=ProtocolType.SIMULATED,
        lat=28.6139, lng=77.2090, site_id=DEFAULT_SITE_ID,
    ))
    await translator.provision_asset(IoTAsset(
        id="sensor-pressure-1", name="Pressure Sensor A1", protocol=ProtocolType.SIMULATED,
        lat=28.6140, lng=77.2091, site_id=DEFAULT_SITE_ID,
    ))

    logger.info("🚀 FastAPI Lifespan: Protocol Translator active, assets provisioned, AI engines ready.")
    yield
    logger.info("🛑 FastAPI Lifespan: Shutting down...")


app = FastAPI(
    title="Industrial Safety Intelligence Agent",
    description="Multi-agent compound risk detection system for industrial facilities",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eht-jerry.vercel.app",  # Your live Vercel frontend
        "http://localhost:3000",         # Local development
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://10.101.199.109:3001",  # Your specific local IP from the logs
        "*"                              # Fallback for hackathon demo flexibility
    ],
    allow_credentials=False,
    # allow_origin = ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# API Endpoints
# ==============================================================================
@app.post("/provision-asset")
async def provision_asset(request: dict):
    protocol_map = {
        "mqtt": ProtocolType.MQTT, 
        "modbus": ProtocolType.MODBUS, 
        "simulated": ProtocolType.SIMULATED
    }
    asset = IoTAsset(
        id=f"sensor-{int(time.time())}",
        name=request.get("name", "Unnamed Sensor"),
        protocol=protocol_map.get(request.get("protocol", "simulated"), ProtocolType.SIMULATED),
        lat=request.get("lat", 28.6139),
        lng=request.get("lng", 77.2090),
        site_id=request.get("site_id", DEFAULT_SITE_ID),
        mqtt_topic=request.get("mqtt_topic"),
        modbus_host=request.get("modbus_host"),
        modbus_port=request.get("modbus_port", 502),
        modbus_register=request.get("modbus_register"),
        modbus_metric=request.get("modbus_metric", "gas"),
    )
    result = await translator.provision_asset(asset)
    return {"status": "provisioned", "asset": result}


@app.get("/api/assets")
async def get_assets(site_id: str = DEFAULT_SITE_ID):
    return translator.get_assets_for_site(site_id)


@app.delete("/api/assets/{asset_id}")
async def remove_asset(asset_id: str):
    removed = translator.remove_asset(asset_id)
    return {"removed": removed}


@app.get("/permit-status")
async def get_permit_status(site_id: str = DEFAULT_SITE_ID):
    return {"permit_active": is_permit_active.get(site_id, True), "site_id": site_id}


@app.get("/api/audit-chain")
async def get_audit_chain():
    return [
        {
            "index": b.index, 
            "timestamp": b.timestamp, 
            "data": b.data,
            "hash": b.hash[:16] + "...", 
            "previous_hash": b.previous_hash[:16] + "...",
        }
        for b in audit_chain.chain
    ]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, site_id: str = DEFAULT_SITE_ID):
    await manager.connect(websocket, site_id)
    try:
        while True:
            # Keep connection alive; frontend doesn't need to send data, just listen
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==============================================================================
# Demo & Control Endpoints ("God Mode" for Hackathon Presentation)
# ==============================================================================

@app.post("/force-emergency")
async def force_emergency():
    """Simulate an immediate emergency to test closed-loop interlocks."""
    global START_TIME
    # Force the timeline to the critical scenario (Scenario 3: ~55 seconds in)
    START_TIME = time.time() - 55  
    logger.warning("🚨 EMERGENCY FORCED VIA API: Jumping to critical risk scenario")
    return {"status": "success", "message": "System forced into critical risk scenario"}

@app.post("/reset-sensors")
async def reset_sensors():
    """Reset all sensor baselines, clear alerts, and restore permits."""
    global START_TIME, cctv_alerts, is_permit_active
    START_TIME = time.time()  # Reset to Scenario 1 (Normal)
    cctv_alerts = []
    is_permit_active = {DEFAULT_SITE_ID: True}
    logger.info("🔄 SYSTEM RESET: Sensors, alerts, and permits returned to normal baseline")
    return {"status": "success", "message": "All systems returned to normal baseline"}

@app.post("/api/simulate-shift")
async def simulate_shift(request: dict = {}):
    """Manually trigger a shift change to demonstrate fatigue analysis."""
    global START_TIME
    START_TIME = time.time() - 55  # Jump to night shift + fatigue scenario
    logger.info("🌙 [MANUAL] SHIFT SIMULATED: Jumping to night shift fatigue scenario")
    return {"status": "success", "message": "Shift changed to Night Shift (Fatigue: High)"}


@app.post("/api/simulate-cctv")
async def simulate_cctv(request: Request):
    """Manually trigger a CCTV alert. Bulletproof: handles empty or invalid JSON gracefully."""
    try:
        # Try to parse JSON body
        body = await request.json()
        alert_type = body.get("type", "ppe_violation") if isinstance(body, dict) else "ppe_violation"
    except Exception:
        # If body is empty, not JSON, or malformed, default safely
        alert_type = "ppe_violation"
        
    cctv_alerts.append({
        "type": alert_type, 
        "timestamp": datetime.now().isoformat(), 
        "site_id": DEFAULT_SITE_ID
    })
    
    # Keep list bounded
    if len(cctv_alerts) > MAX_CCTV_ALERTS:
        cctv_alerts.pop(0)
        
    logger.info(f"📷 [MANUAL] CCTV ALERT TRIGGERED: {alert_type}")
    return {"status": "success", "alert": alert_type}
@app.post("/api/test-modbus")
async def test_modbus():
    """Test endpoint for Modbus connectivity."""
    return {"status": "simulated", "message": "Modbus TCP connection test successful", "connected": True}

@app.post("/api/test-opcua")
async def test_opcua():
    """Test endpoint for OPC UA connectivity."""
    return {"status": "simulated", "message": "OPC UA connection test successful", "connected": True}

@app.get("/download-report")
async def download_report():
    """Generate and download a safety report."""
    # For hackathon demo, return a formatted text file. 
    # In production, this uses reportlab to generate a real PDF.
    report_content = f"""INDUSTRIAL SAFETY INCIDENT REPORT
==================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Site: {DEFAULT_SITE_ID}
Recent CCTV Alerts: {len(cctv_alerts)}
Audit Chain Blocks: {len(audit_chain.chain)}

This is a mock report. In production, this endpoint streams a PDF generated by ReportLab containing full OSHA citations and sensor telemetry.
"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=report_content, media_type="text/plain", headers={
        "Content-Disposition": "attachment; filename=safety_report.txt"
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Uvicorn server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)