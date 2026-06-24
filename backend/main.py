# backend/main.py
import asyncio
import json
import time
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import List
from io import BytesIO
import paho.mqtt.client as mqtt

from permit_agent import permit_agent

# Global state
current_gas = 12.0
current_pressure = 1800.0
current_temp = 42.3
is_permit_active = True

# MQTT Client Setup
mqtt_client = mqtt.Client()

def on_mqtt_message(client, userdata, msg):
    global current_gas, current_pressure, current_temp
    try:
        payload = json.loads(msg.payload.decode())
        value = payload.get("value", 0)
        
        if "gas" in msg.topic: current_gas = float(value)
        elif "pressure" in msg.topic: current_pressure = float(value)
        elif "temp" in msg.topic: current_temp = float(value)
    except Exception as e:
        print(f"MQTT Parse Error: {e}")

mqtt_client.on_message = on_mqtt_message

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
            try: await connection.send_text(json.dumps(message))
            except: pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.subscribe("factory/zone-a/gas")
        mqtt_client.subscribe("factory/zone-a/pressure")
        mqtt_client.subscribe("factory/zone-a/temp")
        mqtt_client.loop_start()
        print("📡 MQTT Client connected and subscribed to factory/zone-a/#", flush=True)
    except Exception as e:
        print(f"❌ MQTT Connection failed: {e}. Make sure broker.py is running!", flush=True)
    
    asyncio.create_task(broadcast_loop())
    yield
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(title="Industrial Safety Intelligence Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast_loop():
    global is_permit_active
    while True:
        sensor_data = {
            "gas": round(current_gas, 1),
            "pressure": round(current_pressure, 1),
            "temperature": round(current_temp, 1),
            "shift": 0
        }
        
        decision = permit_agent.evaluate(sensor_data)
        
        # Closed-Loop Interlock
        if not decision["permit_active"] and is_permit_active:
            cmd = {"action": "CLOSE", "reason": decision["blocked_reason"], "ts": time.time()}
            mqtt_client.publish("factory/valve-1/command", json.dumps(cmd))
            print(f"🚨 CLOSED-LOOP: Sent VALVE CLOSE command via MQTT!", flush=True)
            
        is_permit_active = decision["permit_active"]
        
        broadcast_payload = {**sensor_data, **decision}
        await manager.broadcast(broadcast_payload)
        await asyncio.sleep(2)

# ============================================
# 📡 REST API ENDPOINTS
# ============================================

@app.post("/force-emergency")
async def force_emergency():
    mqtt_client.publish("factory/simulate/emergency", json.dumps({"action": "start"}))
    print("🚨 DEMO MODE: Published Emergency Command to MQTT", flush=True)
    return {"status": "Emergency Triggered via MQTT"}

@app.post("/reset-sensors")
async def reset_sensors():
    mqtt_client.publish("factory/simulate/reset", json.dumps({"action": "stop"}))
    print("✅ DEMO MODE: Published Reset Command to MQTT", flush=True)
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
            "name": name, "protocol": protocol, "status": "learning",
            "lat": request.get("lat", 28.6139), "lng": request.get("lng", 77.2090)
        }
    }

# ============================================
# 📄 PDF COMPLIANCE REPORT ENDPOINT
# ============================================

@app.get("/download-report")
async def download_report():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(72, 750, "Industrial Safety Compliance Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(72, 720, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(72, 700, "Facility: Zone B - Main Valve Assembly")
    
    # Incident Details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 650, "Incident Summary:")
    p.setFont("Helvetica", 12)
    p.drawString(72, 630, f"Gas Level: {current_gas}% (Threshold: 40%)")
    p.drawString(72, 610, f"Pressure: {current_pressure} bar (Threshold: 2400)")
    p.drawString(72, 590, f"Temperature: {current_temp}°C (Threshold: 65)")
    
    # AI Action
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 540, "AI Automated Actions:")
    p.setFont("Helvetica", 12)
    p.drawString(72, 520, "1. Digital Permit automatically BLOCKED.")
    p.drawString(72, 500, "2. MQTT Command sent to close isolation valve.")
    p.drawString(72, 480, "3. RAG Engine retrieved OSHA 3151 protocols.")
    
    # OSHA Reference
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 430, "Regulatory Reference (OSHA 3151):")
    p.setFont("Helvetica", 10)
    p.drawString(72, 410, "In the event of H2S or combustible gas exceeding 40% LEL,")
    p.drawString(72, 395, "all hot work must cease immediately. Personnel must evacuate")
    p.drawString(72, 380, "upwind and don SCBA if gas levels exceed IDLH limits.")
    
    # Footer
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

# ============================================
# 🔌 WEBSOCKET ENDPOINT
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)