# backend/mock_sensor.py
"""
Mock IoT Sensor (Terminal 2)
Simulates physical hardware on the factory floor.
Publishes sensor data and listens for actuator commands from the AI backend.
"""
import paho.mqtt.client as mqtt
import time
import random
import json

# Initialize MQTT Client
client = mqtt.Client()
client.connect("localhost", 1883, 60)

# State variables
force_emergency = False

# Phase 2: Listen for hardware commands & demo triggers
def on_message(client, userdata, msg):
    global force_emergency
    
    # Handle Actuator Commands (Closed-Loop Interlock)
    if "command" in msg.topic:
        cmd = json.loads(msg.payload.decode())
        # EXACT PRINT STATEMENT FROM EXECUTION PLAN
        print(f"\n⚠️  HARDWARE CMD RECEIVED → {cmd['action']} (reason: {cmd['reason']})\n")
        
    # Handle Demo Triggers from Frontend
    elif "emergency" in msg.topic:
        force_emergency = True
        print("\n🚨 RECEIVED SIMULATE EMERGENCY COMMAND - SPIKING DATA\n")
        
    elif "reset" in msg.topic:
        force_emergency = False
        print("\n✅ RECEIVED RESET COMMAND - RETURNING TO NORMAL\n")

# Subscribe to commands and demo triggers
client.subscribe("factory/+/command")
client.subscribe("factory/simulate/emergency")
client.subscribe("factory/simulate/reset")
client.on_message = on_message

# Start the MQTT network loop in the background
client.loop_start()

print("🎮 Mock IoT Sensor started. Publishing to MQTT broker...")
print("📡 Topics: factory/zone-a/gas, factory/zone-a/pressure, factory/zone-a/temp")

try:
    while True:
        # Generate data based on current state
        if force_emergency:
            # Dangerous levels to trigger the AI
            gas = random.uniform(75, 95)
            pressure = random.uniform(2500, 2800)
            temp = random.uniform(70, 85)
        else:
            # Normal safe levels
            gas = random.uniform(10, 35)
            pressure = random.uniform(1700, 2100)
            temp = random.uniform(40, 60)
        
        # Publish to MQTT Broker (Phase 1)
        client.publish("factory/zone-a/gas", json.dumps({"value": round(gas, 1)}))
        client.publish("factory/zone-a/pressure", json.dumps({"value": round(pressure, 1)}))
        client.publish("factory/zone-a/temp", json.dumps({"value": round(temp, 1)}))
        
        # Optional: Print a small status line so judges see it's alive
        print(f"📤 Published -> Gas: {round(gas,1)}% | Pressure: {round(pressure,0)} bar | Temp: {round(temp,1)}°C")
        
        # Wait 2 seconds before next reading (matches your backend broadcast rate)
        time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Mock Sensor stopped by user.")
    client.loop_stop()
    client.disconnect()