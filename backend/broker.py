# backend/broker.py
import asyncio
from amqtt.broker import Broker

# We add "sys_interval": 10 back to prevent the NoneType crash in the sys plugin
broker_config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        },
    },
    "sys_interval": 10,  
    "auth": {
        "allow-anonymous": True,
    }
}

async def run_broker():
    print("🚀 Starting local MQTT Broker on port 1883...")
    broker = Broker(config=broker_config)
    await broker.start()
    print("✅ MQTT Broker is running. Waiting for connections...")
    
    # Keep the broker alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(run_broker())
    except KeyboardInterrupt:
        print("\n🛑 MQTT Broker stopped.")