import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from permit_agent import permit_agent

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

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

async def generate_sensor_data():
    gas = 12.0
    pressure = 1800.0
    temp = 42.3
    
    print(" Mock sensor simulator started successfully!")
    
    while True:
        gas += random.uniform(-0.5, 1.8)
        gas = max(0.0, min(100.0, gas))
        
        pressure += random.uniform(-15, 15)
        pressure = max(1600.0, min(2800.0, pressure))
        
        temp += random.uniform(-0.3, 0.4)
        temp = max(30.0, min(80.0, temp))
        
        sensor_data = {
            "gas": round(gas, 1),
            "pressure": round(pressure, 0),
            "temperature": round(temp, 1),
            "shift": 0
        }
        
        agent_decision = permit_agent.evaluate_conditions(sensor_data)
        broadcast_payload = {**sensor_data, **agent_decision}
        
        if not agent_decision["permit_active"]:
            print(f"🚨 PERMIT BLOCKED! Reason: {agent_decision['blocked_reason']}")
        
        await manager.broadcast(broadcast_payload)
        await asyncio.sleep(2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
