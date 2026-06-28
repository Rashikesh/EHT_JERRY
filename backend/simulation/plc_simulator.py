
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import random

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

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
    """Simulates realistic sensor data with occasional danger spikes"""
    gas = 12.0
    pressure = 1800.0
    temp = 42.3
    
    print("🎮 Starting sensor data simulator...")
    print("📊 Watch gas levels drift - when it exceeds 40%, the permit will be BLOCKED!")
    
    while True:
        # Simulate gradual drift with occasional spikes
        gas_change = random.uniform(-0.5, 1.8)  # Bias towards increasing
        gas = max(0, min(100, gas + gas_change))
        
        pressure = max(1600, min(2800, pressure + random.uniform(-15, 15)))
        temp = max(30, min(80, temp + random.uniform(-0.3, 0.4)))
        
        data = {
            "gas": round(gas, 1),
            "pressure": round(pressure, 0),
            "temperature": round(temp, 1),
            "shift": 0
        }
        
        alert = "⚠️ " if gas > 30 else ""
        if gas > 40:
            alert = "🚨 CRITICAL - PERMIT BLOCKED! "
        
        print(f"{alert}Gas: {data['gas']}% | Pressure: {data['pressure']} bar | Temp: {data['temperature']}°C")
        
        await manager.broadcast(data)
        await asyncio.sleep(2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
