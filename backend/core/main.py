import sys
import os

# Ensure backend root is in Python path for clean imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from io import BytesIO

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse

# --- AI & Core Modules ---
from core.audit_chain import audit_chain
from ai.predictive_analyzer import predictive_analyzer
from ai.cctv_simulator import cctv_simulator
from ai.shift_analyzer import shift_analyzer
from ai.incident_matcher import incident_matcher
from ai.anomaly_detector import anomaly_detector
from ai.compound_risk_engine import compound_risk_engine, TemporalEvent

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
START_TIME = time.time()


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
# Visakhapatnam Scenario Driver
# ==============================================================================
async def run_visakhapatnam_scenario(gas_value: float) -> dict:
    """Drives the specific T+0 to T+20 minute demo timeline."""
    global START_TIME  # ⚠️ MUST BE THE VERY FIRST LINE INSIDE THE FUNCTION
    
    elapsed = time.time() - START_TIME
    
    # T+0:00 to T+0:05 (0-300s): Normal gas, Permit issued
    if elapsed < 300:
        if elapsed < 10: # Only log once
            compound_risk_engine.ingest_event(TemporalEvent(
                event_type="permit_issued", 
                timestamp=datetime.now(), 
                zone="Zone_A", 
                payload={"permit_type": "confined_space"}
            ))
            compound_risk_engine.timeline_events.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "event": "📝 Permit Issued: Confined Space (Zone A)",
                "detail": "Maintenance crew authorized",
                "type": "PERMIT"
            })
        return {"gas": 12.0, "permit_active": True}

    # T+0:05 to T+0:10 (300-600s): Gas rises to 18%
    elif elapsed < 600:
        return {"gas": 18.0, "permit_active": True}

    # T+0:10 to T+0:15 (600-900s): Gas trends to 25%, Shift changeover
    elif elapsed < 900:
        if 600 < elapsed < 610: # Log once
            compound_risk_engine.ingest_event(TemporalEvent(
                event_type="shift_change", 
                timestamp=datetime.now(), 
                zone="Zone_A", 
                payload={"type": "handoff"}
            ))
            compound_risk_engine.timeline_events.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "event": "🔄 Shift Changeover Begins",
                "detail": "Handoff confusion window",
                "type": "SHIFT"
            })
        return {"gas": 25.0, "permit_active": True}

    # T+0:15 to T+0:20 (900-1200s): Gas hits 35% -> SYSTEM BLOCKS
    elif elapsed < 1200:
        compound_risk_engine.ingest_event(TemporalEvent(
            event_type="gas_reading", 
            timestamp=datetime.now(), 
            zone="Zone_A", 
            payload={"gas_level": 35.0, "trend": "rising"}
        ))
        
        state = compound_risk_engine.get_state()
        is_blocked = len(state["alerts"]) > 0 and state["alerts"][-1]["action"] == "BLOCK_PERMIT"
        
        return {"gas": 35.0, "permit_active": not is_blocked}

    # Reset after 20 minutes (No 'global' keyword needed here anymore)
    else:
        START_TIME = time.time()
        compound_risk_engine.timeline_events = []
        compound_risk_engine.triggered_alerts = []
        return {"gas": 12.0, "permit_active": True}
# ==============================================================================
# Core Data Processing Pipeline
# ==============================================================================
async def on_asset_data(asset: IoTAsset):
    site_id = asset.site_id
    
    global cctv_alerts
    new_alerts = cctv_simulator.check_for_alerts()
    if new_alerts:
        cctv_alerts.extend(new_alerts)
        cctv_alerts = cctv_alerts[-MAX_CCTV_ALERTS:]
        logger.info(f"📷 [{site_id}] CCTV ALERT: {new_alerts[0]['type']}")

    site_assets = translator.get_assets_for_site(site_id)
    gas = next((a["gasLevel"] for a in site_assets if "gas" in a["name"].lower()), asset.current_value)
    pressure = next((a["gasLevel"] for a in site_assets if "pressure" in a["name"].lower()), 0.0)
    temperature = next((a["gasLevel"] for a in site_assets if "temp" in a["name"].lower()), 0.0)
    
    # Run the Visakhapatnam Scenario
    scenario = await run_visakhapatnam_scenario(gas)
    engine_state = compound_risk_engine.get_state()
    
    # Build payload
    broadcast_payload = {
        "site_id": site_id,
        "gas": round(scenario["gas"], 1),
        "pressure": round(pressure, 1),
        "temperature": round(temperature, 1),
        "permit_active": scenario["permit_active"],
        "active_alerts": engine_state["alerts"],
        "timeline_events": engine_state["timeline"],
        "citation": engine_state["alerts"][-1]["citation"] if engine_state["alerts"] else None,
        "ai_justification": engine_state["alerts"][-1]["citation"] if engine_state["alerts"] else "All parameters normal",
        "blocked_reason": engine_state["alerts"][-1]["rule_name"] if engine_state["alerts"] else None
    }
    
    await manager.broadcast(site_id, broadcast_payload)


# ==============================================================================
# FastAPI Application & Lifespan
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    translator.on_data_callback = on_asset_data

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

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# API Endpoints
# ==============================================================================
@app.post("/provision-asset")
async def provision_asset(request: dict):
    protocol_map = {"mqtt": ProtocolType.MQTT, "modbus": ProtocolType.MODBUS, "simulated": ProtocolType.SIMULATED}
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
            "index": b.index, "timestamp": b.timestamp, "data": b.data,
            "hash": b.hash[:16] + "...", "previous_hash": b.previous_hash[:16] + "...",
        }
        for b in audit_chain.chain
    ]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, site_id: str = DEFAULT_SITE_ID):
    await manager.connect(websocket, site_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==============================================================================
# Demo & Control Endpoints ("God Mode")
# ==============================================================================
@app.post("/force-emergency")
async def force_emergency():
    global START_TIME
    START_TIME = time.time() - 1100  # Jump to T+18 mins (Critical Block)
    logger.warning("🚨 EMERGENCY FORCED VIA API: Jumping to critical risk scenario")
    return {"status": "success", "message": "System forced into critical risk scenario"}

@app.post("/reset-sensors")
async def reset_sensors():
    global START_TIME, cctv_alerts, is_permit_active
    START_TIME = time.time()
    cctv_alerts = []
    is_permit_active = {DEFAULT_SITE_ID: True}
    logger.info("🔄 SYSTEM RESET: Sensors, alerts, and permits returned to normal baseline")
    return {"status": "success", "message": "All systems returned to normal baseline"}

@app.post("/api/simulate-cctv")
async def simulate_cctv(request: Request):
    try:
        body = await request.json()
        alert_type = body.get("type", "ppe_violation") if isinstance(body, dict) else "ppe_violation"
    except Exception:
        alert_type = "ppe_violation"
        
    cctv_alerts.append({"type": alert_type, "timestamp": datetime.now().isoformat(), "site_id": DEFAULT_SITE_ID})
    if len(cctv_alerts) > MAX_CCTV_ALERTS:
        cctv_alerts.pop(0)
    logger.info(f"📷 [MANUAL] CCTV ALERT TRIGGERED: {alert_type}")
    return {"status": "success", "alert": alert_type}

@app.post("/api/test-modbus")
async def test_modbus():
    return {"status": "simulated", "message": "Modbus TCP connection test successful", "connected": True}

@app.post("/api/test-opcua")
async def test_opcua():
    return {"status": "simulated", "message": "OPC UA connection test successful", "connected": True}

@app.get("/download-report")
async def download_report():
    report_content = f"""INDUSTRIAL SAFETY INCIDENT REPORT
==================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Site: {DEFAULT_SITE_ID}
Recent CCTV Alerts: {len(cctv_alerts)}
Audit Chain Blocks: {len(audit_chain.chain)}
"""
    return PlainTextResponse(content=report_content, media_type="text/plain", headers={
        "Content-Disposition": "attachment; filename=safety_report.txt"
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Uvicorn server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)