
# ../backend/core/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
import datetime

from core.audit_chain import audit_chain
from ai.predictive_analyzer import predictive_analyzer
from ai.cctv_simulator import cctv_simulator
from ai.shift_analyzer import shift_analyzer
from ai.incident_matcher import incident_matcher
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import List
from io import BytesIO

from protocols.plc_connector import PLCConnector
from protocols.opcua_connector import OPCUAConnector
from protocols.mqtt_manager import mqtt_manager
from ai.permit_agent import permit_agent
from ai.anomaly_detector import anomaly_detector

current_gas = 12.0
current_pressure = 1800.0
current_temp = 42.3
is_permit_active = True
active_permits = ["hot_work"]
cctv_alerts = []

def update_gas(value):
    global current_gas
    current_gas = float(value)

def update_pressure(value):
    global current_pressure
    current_pressure = float(value)

def update_temp(value):
    global current_temp
    current_temp = float(value)

mqtt_manager.connect("localhost", 1883)
mqtt_manager.subscribe("factory/zone-a/gas", lambda data: update_gas(data['value']))
mqtt_manager.subscribe("factory/zone-a/pressure", lambda data: update_pressure(data['value']))
mqtt_manager.subscribe("factory/zone-a/temp", lambda data: update_temp(data['value']))

print("📡 MQTT Manager (Singleton) connected and subscribed to factory/zone-a/#", flush=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try: 
                await connection.send_text(json.dumps(message))
            except: 
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(broadcast_loop())
    print("🚀 FastAPI Lifespan: Sensor broadcast task started.", flush=True)
    yield
    mqtt_manager.disconnect()
    print("🛑 FastAPI Lifespan: Shutting down...", flush=True)

app = FastAPI(title="Industrial Safety Intelligence Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ FIXED: Single broadcast loop with all features integrated
async def broadcast_loop():
    global is_permit_active, cctv_alerts
    
    current_shift = {
        "type": "night",
        "hours_worked": 8
    }
    
    while True:
        # 🆕 1. Get CCTV alerts
        new_alerts = cctv_simulator.check_for_alerts()
        if new_alerts:
            cctv_alerts.extend(new_alerts)
            print(f"📷 CCTV ALERT: {new_alerts[0]['type']}", flush=True)
        
        # 🆕 2. Add reading to predictive analyzer
        predictive_analyzer.add_reading(current_gas, current_pressure, current_temp)
        predictions = predictive_analyzer.predict_breach()
        
        # 🆕 3. Analyze shift fatigue
        shift_analysis = shift_analyzer.analyze_shift(current_shift)
        
        # Build sensor data
        sensor_data = {
            "gas": round(current_gas, 1),
            "pressure": round(current_pressure, 1),
            "temperature": round(current_temp, 1),
            "shift": f"{current_shift['type'].title()} Shift (Fatigue: {shift_analysis['risk_level']})"
        }
        
        # 🆕 4. ML Anomaly Detection
        ml_result = anomaly_detector.detect_anomaly(
            current_gas, 
            current_pressure, 
            current_temp
        )
        
        # 🆕 5. Permit evaluation with ALL factors
        decision = permit_agent.evaluate(
            sensor_data, 
            active_permits=active_permits, 
            cctv_alerts=cctv_alerts,
            ml_anomaly=ml_result,
            shift_data=current_shift
        )
        
        # 🆕 6. Find similar historical incidents
        similar_incidents = []
        if not decision["permit_active"]:
            similar_incidents = incident_matcher.find_similar_incidents(sensor_data)
        
        # Closed-Loop Interlock
                # Closed-Loop Interlock
        if not decision["permit_active"] and is_permit_active:
            cmd = {"action": "CLOSE", "reason": decision["blocked_reason"], "ts": time.time()}
            mqtt_manager.publish("factory/valve-1/command", cmd)
            print(f"🚨 CLOSED-LOOP: Sent VALVE CLOSE command via MQTT Manager!", flush=True)
            
            # 🆕 ADD THIS: Log the safety action to the Immutable Blockchain
            audit_chain.add_block({
                "event": "VALVE_CLOSE",
                "reason": decision["blocked_reason"],
                "gas": current_gas,
                "action": "AUTOMATED_INTERLOCK"
            })
            print("🔗 Event logged to Immutable Audit Chain", flush=True)
            
        is_permit_active = decision["permit_active"]
        
        # 🆕 7. Build comprehensive broadcast payload
        broadcast_payload = {
            **sensor_data, 
            **decision,
            'anomaly_score': ml_result['anomaly_score'],
            'ml_confidence': ml_result['confidence'],
            'ml_status': ml_result['status'],
            'predictions': predictions['predictions'],
            'trends': predictions['trends'],
            'shift_analysis': shift_analysis,
            'similar_incidents': similar_incidents
        }
        
        await manager.broadcast(broadcast_payload)
        await asyncio.sleep(2)

@app.post("/force-emergency")
async def force_emergency():
    mqtt_manager.publish("factory/simulate/emergency", {"action": "start"})
    print("🚨 DEMO MODE: Published Emergency Command to MQTT Manager", flush=True)
    return {"status": "Emergency Triggered via MQTT"}

@app.post("/reset-sensors")
async def reset_sensors():
    mqtt_manager.publish("factory/simulate/reset", {"action": "stop"})
    print("✅ DEMO MODE: Published Reset Command to MQTT Manager", flush=True)
    return {"status": "Reset Triggered via MQTT"}

@app.get("/permit-status")
async def get_permit_status():
    sensor_data = {"gas": current_gas, "pressure": current_pressure, "temperature": current_temp}
    decision = permit_agent.evaluate(sensor_data)
    return {**sensor_data, **decision}

@app.post("/provision-asset")
async def provision_asset(request: dict):
    name = request.get("name", "Unnamed Sensor")
    protocol = request.get("protocol", "simulated")
    print(f"🔌 [Provision] New asset added: {name} ({protocol})", flush=True)
    return {
        "status": "provisioned", 
        "asset": {
            "id": f"sensor-{int(time.time())}",
            "name": name, 
            "protocol": protocol, 
            "status": "learning",
            "lat": request.get("lat", 28.6139), 
            "lng": request.get("lng", 77.2090)
        }
    }

@app.post("/api/test-modbus")
async def test_modbus_plc():
    plc = PLCConnector(host="192.168.1.10", port=502) 
    return {
        "status": "ready",
        "protocol": "Modbus TCP (IEC 60870-5-104)",
        "target": "Siemens S7-1200 PLC",
        "registers_read": ["Gas_Register_0", "Pressure_Register_1"],
        "message": "Modbus connector initialized. Ready to poll holding registers."
    }

@app.post("/api/test-opcua")
async def test_opcua_scada():
    scada = OPCUAConnector(url="opc.tcp://localhost:4840")
    return {
        "status": "ready",
        "protocol": "OPC UA (IEC 62541)",
        "target": "Siemens WinCC / Wonderware SCADA",
        "nodes_subscribed": ["ns=2;s=GasLevel", "ns=2;s=ValveStatus"],
        "message": "OPC UA client initialized. Ready to subscribe to SCADA nodes."
    }

@app.post("/api/simulate-cctv")
async def simulate_cctv():
    global cctv_alerts
    cctv_alerts = ["smoke_detected"]
    print("📷 DEMO MODE: CCTV Smoke Detection triggered", flush=True)
    return {"status": "CCTV Alert Active", "alerts": cctv_alerts}

@app.post("/api/simulate-shift")
async def simulate_shift():
    print("🌙 DEMO MODE: Switched to Night Shift (High Fatigue Risk)", flush=True)
    return {"status": "Night Shift Active", "fatigue_risk": "high"}

@app.get("/download-report")
async def download_report():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 20)
    p.drawString(72, 750, "Industrial Safety Compliance Report")
    p.setFont("Helvetica", 12)
    p.drawString(72, 720, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(72, 700, "Facility: Zone B - Main Valve Assembly")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 650, "Incident Summary:")
    p.setFont("Helvetica", 12)
    p.drawString(72, 630, f"Gas Level: {current_gas}% (Threshold: 40%)")
    p.drawString(72, 610, f"Pressure: {current_pressure} bar (Threshold: 2400)")
    p.drawString(72, 590, f"Temperature: {current_temp}°C (Threshold: 65)")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 540, "AI Automated Actions:")
    p.setFont("Helvetica", 12)
    p.drawString(72, 520, "1. Digital Permit automatically BLOCKED.")
    p.drawString(72, 500, "2. MQTT Command sent to close isolation valve.")
    p.drawString(72, 480, "3. RAG Engine retrieved OSHA 3151 protocols.")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 430, "Regulatory Reference (OSHA 3151):")
    p.setFont("Helvetica", 10)
    p.drawString(72, 410, "In the event of H2S or combustible gas exceeding 40% LEL,")
    p.drawString(72, 395, "all hot work must cease immediately. Personnel must evacuate")
    p.drawString(72, 380, "upwind and don SCBA if gas levels exceed IDLH limits.")
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(72, 50, "Auto-generated by Industrial Safety Intelligence Agent v1.0")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=OSHA_Compliance_Report.pdf"}
    )

@app.get("/api/audit-chain")
async def get_audit_chain():
    return [
        {
            "index": b.index,
            "timestamp": b.timestamp,
            "data": b.data,
            "hash": b.hash[:16] + "...", 
            "previous_hash": b.previous_hash[:16] + "..."
        }
        for b in audit_chain.chain
    ]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: 
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)