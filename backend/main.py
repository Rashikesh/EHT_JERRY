import asyncio
import random
import sys
from data_validator import DataValidator
from anomaly_detector import AnomalyDetector
from sensor_filter import SensorFilter
from audit_logger import log_decision
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from permit_agent import permit_agent

# Initialize globally
sensor_filter = SensorFilter(window_size=5)
anomaly_detector = AnomalyDetector()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected! Total: {len(self.active_connections)}", flush=True)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ Client disconnected! Total: {len(self.active_connections)}", flush=True)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ Send failed: {e}", flush=True)
                dead_connections.append(connection)
        for conn in dead_connections:
            self.disconnect(conn)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(generate_sensor_data())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}", flush=True)
        manager.disconnect(websocket)

async def generate_sensor_data():
    print("🔥 GENERATE_SENSOR_DATA STARTED!", flush=True)
    
    gas = 12.0
    pressure = 1800.0
    temp = 42.3
    
    print("🎮 Mock sensor simulator started!", flush=True)
    
    counter = 0
    while True:
        try:
            counter += 1
            print(f"\n🔄 --- ITERATION {counter} ---", flush=True)
            
            # 1. Generate raw values
            gas += random.uniform(-0.5, 1.8)
            gas = max(0.0, min(100.0, gas))
            pressure += random.uniform(-15, 15)
            pressure = max(1600.0, min(2800.0, pressure))
            temp += random.uniform(-0.3, 0.4)
            temp = max(30.0, min(80.0, temp))
            
            raw_data = {
                "gas": round(gas, 1),
                "pressure": round(pressure, 0),
                "temperature": round(temp, 1),
                "shift": 0
            }
            print(f"📊 Raw: Gas={raw_data['gas']}%", flush=True)
            
            # 2. Validate
            is_valid, error_msg = DataValidator.validate_sensor_data(raw_data)
            if not is_valid:
                print(f"️ REJECTED: {error_msg}", flush=True)
                await asyncio.sleep(2)
                continue
            
            # 3. Filter
            filtered = sensor_filter.filter_reading(
                raw_data['gas'], raw_data['pressure'], raw_data['temperature']
            )
            
            # 4. Anomaly check
            is_anomaly, mean, std = anomaly_detector.check_anomaly(filtered['gas_smooth'])
            if is_anomaly:
                print(f"️ ANOMALY: Gas={filtered['gas_smooth']:.1f}%", flush=True)
            
            # 5. Build sensor data (ONCE)
            sensor_data = {
                "gas": round(filtered['gas_smooth'], 1),
                "pressure": round(filtered['pressure_smooth'], 0),
                "temperature": round(filtered['temp_smooth'], 1),
                "shift": 0,
                "anomaly_detected": is_anomaly
            }
            print(f"📈 Smoothed: Gas={sensor_data['gas']}%", flush=True)
            
            # 6. AI Decision
            print("🤖 Evaluating conditions...", flush=True)
            agent_decision = permit_agent.evaluate_conditions(sensor_data)
            
            # 7. Log
            log_decision(sensor_data, agent_decision)
            
            # 8. Build payload
            broadcast_payload = {**sensor_data, **agent_decision}
            print(f"📦 Payload keys: {list(broadcast_payload.keys())}", flush=True)
            
            # 9. Broadcast
            print(f" Broadcasting to {len(manager.active_connections)} clients", flush=True)
            await manager.broadcast(broadcast_payload)
            
            if not agent_decision["permit_active"]:
                print(f"🚨 PERMIT BLOCKED!", flush=True)
            
            print(f"✅ Iteration {counter} complete", flush=True)
            
        except Exception as e:
            print(f"💥 ERROR IN LOOP: {e}", flush=True)
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)