import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
import datetime
import logging

from core.audit_chain import audit_chain
from ai.predictive_analyzer import predictive_analyzer
from ai.cctv_simulator import cctv_simulator
from ai.shift_analyzer import shift_analyzer
from ai.incident_matcher import incident_matcher
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import List, Dict
from io import BytesIO

from protocols.protocol_translator import translator, IoTAsset, ProtocolType, SensorStatus
from ai.permit_agent import permit_agent
from ai.anomaly_detector import anomaly_detector

logger = logging.getLogger("safety_agent")
logging.basicConfig(level=logging.INFO)

DEFAULT_SITE_ID = "site-a"
MAX_CCTV_ALERTS = 50
cctv_alerts: List[dict] = []
is_permit_active: Dict[str, bool] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_site: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, site_id: str = DEFAULT_SITE_ID):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_site[websocket] = site_id

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.connection_site.pop(websocket, None)

    async def broadcast(self, site_id: str, message: dict):
        for connection in list(self.active_connections):
            if self.connection_site.get(connection) != site_id:
                continue
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass


manager = ConnectionManager()


# 🆕 This is the ONE place live sensor data enters the rest of the pipeline —
# called by ProtocolTranslator every time ANY asset (MQTT, Modbus, simulated)
# gets a new reading. Ingestion and processing are now fully decoupled:
# translator handles reading fast; this callback handles the "slow" work.
async def on_asset_data(asset: IoTAsset):
    site_id = asset.site_id

    global cctv_alerts
    new_alerts = cctv_simulator.check_for_alerts()
    if new_alerts:
        cctv_alerts.extend(new_alerts)
        cctv_alerts = cctv_alerts[-MAX_CCTV_ALERTS:]
        logger.info(f"📷 [{site_id}] CCTV ALERT: {new_alerts[0]['type']}")

    # Pull latest values for this site across all its assets
    site_assets = translator.get_assets_for_site(site_id)
    gas = next((a["gasLevel"] for a in site_assets if "gas" in a["name"].lower()), asset.current_value)
    pressure = next((a["gasLevel"] for a in site_assets if "pressure" in a["name"].lower()), 0.0)
    temperature = next((a["gasLevel"] for a in site_assets if "temp" in a["name"].lower()), 0.0)

    predictive_analyzer.add_reading(gas, pressure, temperature)
    predictions = predictive_analyzer.predict_breach()
    shift_analysis = shift_analyzer.analyze_shift({"type": "night", "hours_worked": 8})

    sensor_data = {
        "site_id": site_id,
        "gas": round(gas, 1),
        "pressure": round(pressure, 1),
        "temperature": round(temperature, 1),
        "shift": f"Night Shift (Fatigue: {shift_analysis['risk_level']})",
    }

    ml_result = anomaly_detector.detect_anomaly(gas, pressure, temperature)

    decision = permit_agent.evaluate(
        sensor_data,
        active_permits=["hot_work"],
        cctv_alerts=cctv_alerts,
        ml_anomaly=ml_result,
        shift_data={"type": "night", "hours_worked": 8},
    )

    similar_incidents = []
    if not decision["permit_active"]:
        similar_incidents = incident_matcher.find_similar_incidents(sensor_data)

    was_active = is_permit_active.get(site_id, True)
    if not decision["permit_active"] and was_active:
        logger.warning(f"🚨 [{site_id}] CLOSED-LOOP: permit blocked — {decision['blocked_reason']}")
        audit_chain.add_block({
            "site_id": site_id,
            "event": "VALVE_CLOSE",
            "reason": decision["blocked_reason"],
            "gas": gas,
            "action": "AUTOMATED_INTERLOCK",
        })
        logger.info(f"🔗 [{site_id}] Event logged to Immutable Audit Chain")

    is_permit_active[site_id] = decision["permit_active"]

    broadcast_payload = {
        **sensor_data,
        **decision,
        "anomaly_score": ml_result["anomaly_score"],
        "ml_confidence": ml_result["confidence"],
        "ml_status": ml_result["status"],
        "predictions": predictions["predictions"],
        "trends": predictions["trends"],
        "shift_analysis": shift_analysis,
        "similar_incidents": similar_incidents,
    }

    # TODO once DB session is wired: persist sensor_data + decision to SensorReading table here

    await manager.broadcast(site_id, broadcast_payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    translator.on_data_callback = on_asset_data

    # 🆕 Demo default: one simulated asset per metric, site-a.
    # Swap protocol=ProtocolType.MODBUS + modbus_host="192.168.1.10" for real PLC.
    await translator.provision_asset(IoTAsset(
        id="sensor-gas-1", name="Gas Sensor A1", protocol=ProtocolType.SIMULATED,
        lat=28.6139, lng=77.2090, site_id=DEFAULT_SITE_ID,
    ))

    logger.info("🚀 FastAPI Lifespan: Protocol Translator active, assets provisioned.")
    yield
    logger.info("🛑 FastAPI Lifespan: Shutting down...")


app = FastAPI(title="Industrial Safety Intelligence Agent", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))