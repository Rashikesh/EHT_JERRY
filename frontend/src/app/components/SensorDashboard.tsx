// src/components/SensorDashboard.tsx
"use client"

import { useEffect, useState } from "react"
import PlantMap from "./PlantMap"
import ResizableChart from "./ResizableChart"
import { useLayout } from "@/contexts/LayoutContext"
import "@/styles/dashboard.css"

import ConnectionStatus from "./dashboard/ConnectionStatus"
import DashboardHeader from "./dashboard/DashboardHeader"
import ControlButtons from "./dashboard/ControlButtons"
import SensorGrid from "./dashboard/SensorGrid"
import PermitStatusPanel from "./dashboard/PermitStatusPanel"

// Define the shape of our IoT Assets
interface IoTAsset {
  id: string
  name: string
  lat: number
  lng: number
  status: "learning" | "active" | "critical"
  gasLevel: number
  learnedThreshold: number
}

interface SensorData {
  gas: number
  pressure: number
  temperature: number
  shift: number
  permit_active: boolean
  ai_justification: string
  blocked_reason: string | null
  confidence?: number
  all_reasons?: string[]
}

export default function SensorDashboard() {
  const { chartHeight } = useLayout()

  const [data, setData] = useState<SensorData>({
    gas: 0,
    pressure: 0,
    temperature: 0,
    shift: 0,
    permit_active: true,
    ai_justification: "",
    blocked_reason: null,
  })
  const [status, setStatus] = useState("Connecting to backend...")
  const [chartData, setChartData] = useState<{ time: string; gas: number }[]>(
    [],
  )
  const [systemEvents, setSystemEvents] = useState<
    { time: string; type: string }[]
  >([])

  // 🆕 NEW: State for Plug-and-Play Assets
  const [assets, setAssets] = useState<IoTAsset[]>([
    {
      id: "sensor-1",
      name: "Main Valve A",
      lat: 28.6139,
      lng: 77.209,
      status: "active",
      gasLevel: 12,
      learnedThreshold: 40,
    },
    {
      id: "sensor-2",
      name: "Secondary Pipe B",
      lat: 28.6142,
      lng: 77.2095,
      status: "active",
      gasLevel: 15,
      learnedThreshold: 35,
    },
  ])
  const [showProvisionModal, setShowProvisionModal] = useState(false)

  const calculateRiskScore = () => {
    let score = 0
    score += Math.min(40, (data.gas / 100) * 40)
    const pressureRisk = Math.max(0, (data.pressure - 1600) / 1200)
    score += pressureRisk * 30
    const tempRisk = Math.max(0, (data.temperature - 30) / 50)
    score += tempRisk * 30
    return Math.round(score)
  }

  const riskScore = calculateRiskScore()
  const riskColor = riskScore > 70 ? "red" : riskScore > 40 ? "yellow" : "green"

  //  NEW: Function to simulate Plug-and-Play Provisioning
  const provisionNewAsset = (name: string) => {
    const newAsset: IoTAsset = {
      id: `sensor-${Date.now()}`,
      name: name,
      lat: 28.6135 + Math.random() * 0.001, // Slight random offset
      lng: 77.2085 + Math.random() * 0.001,
      status: "learning", // Starts in Self-Harnessing phase
      gasLevel: 0,
      learnedThreshold: 0,
    }
    setAssets((prev) => [...prev, newAsset])

    // Simulate AI Self-Harnessing (Learning Phase takes 5 seconds)
    setTimeout(() => {
      setAssets((prev) =>
        prev.map((a) =>
          a.id === newAsset.id
            ? { ...a, status: "active", learnedThreshold: 40 }
            : a,
        ),
      )
    }, 5000)
  }

  useEffect(() => {
    const ws = new WebSocket(
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws",
    )
    ws.onopen = () => setStatus("Connected to PLC")
    ws.onmessage = (event) => {
      const parsed = JSON.parse(event.data)
      const now = new Date().toLocaleTimeString()

      setData((prev) => {
        if (prev.permit_active !== parsed.permit_active) {
          const eventType = parsed.permit_active
            ? "PERMIT ACTIVE"
            : "PERMIT BLOCKED"
          setSystemEvents((prevEvents) => [
            ...prevEvents,
            { time: now, type: eventType },
          ])
        }
        return { ...prev, ...parsed }
      })

      setChartData((prev) => {
        const newData = [...prev, { time: now, gas: parsed.gas }]
        return newData.length > 50 ? newData.slice(-50) : newData
      })

      // Update the main sensor's gas level on the map
      setAssets((prev) =>
        prev.map((a) =>
          a.id === "sensor-1"
            ? {
                ...a,
                gasLevel: parsed.gas,
                status: parsed.gas > 40 ? "critical" : "active",
              }
            : a,
        ),
      )
    }
    ws.onclose = () => setStatus("Disconnected")
    ws.onerror = () => setStatus("Connection Error")

    return () => {
      if (
        ws.readyState === WebSocket.OPEN ||
        ws.readyState === WebSocket.CONNECTING
      )
        ws.close()
    }
  }, [])

  return (
    <div className="dashboard-wrapper">
      <div className="w-full h-full space-y-6 flex flex-col pb-8">
        <ConnectionStatus status={status} />
        <DashboardHeader />
        <div className="mb-6">
          <ControlButtons />
        </div>
        <div className="mb-6">
          <SensorGrid
            gas={data.gas}
            pressure={data.pressure}
            temperature={data.temperature}
          />
        </div>

        <div className="mb-6">
          <ResizableChart
            data={chartData}
            events={systemEvents}
            riskScore={riskScore}
            riskColor={riskColor}
          />
        </div>

        {/* Bottom Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 mb-8">
          <div className="lg:col-span-4">
            <PermitStatusPanel
              permitActive={data.permit_active}
              aiJustification={data.ai_justification}
              confidence={data.confidence}
              gas={data.gas} // 👈 Added
              pressure={data.pressure} // 👈 Added
              temperature={data.temperature} // 👈 Added
            />
          </div>

          <div className="lg:col-span-8">
            <div className="glass-card p-6 mb-4 relative">
              <div className="flex justify-between items-center mb-4">
                <h3 className="stat-label">
                  📍 Live Plant Telemetry & Digital Twin
                </h3>
                {/* 🆕 NEW: Plug-and-Play Provisioning Button */}
                <button
                  onClick={() => setShowProvisionModal(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-2"
                >
                  <span className="text-lg"></span> Provision New IoT Asset
                </button>
              </div>

              <div
                className="map-container"
                style={{ height: `${Math.max(350, chartHeight)}px` }}
              >
                <PlantMap assets={assets} isDanger={data.gas > 40} />
              </div>
            </div>
          </div>
        </div>

        {/* 🆕 NEW: Provisioning Modal */}
        {showProvisionModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[1000] flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-2">
                Provision New IoT Asset
              </h2>
              <p className="text-slate-400 text-sm mb-6">
                Connect a new MQTT/Modbus sensor to the Digital Twin. The AI
                will automatically harness its baseline.
              </p>

              <input
                type="text"
                placeholder="Asset Name (e.g., Boiler Valve 3)"
                className="w-full bg-slate-800 border border-slate-700 text-white p-3 rounded-lg mb-4 focus:outline-none focus:border-blue-500"
                id="assetNameInput"
              />

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowProvisionModal(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    const name =
                      (
                        document.getElementById(
                          "assetNameInput",
                        ) as HTMLInputElement
                      ).value || "New Sensor"
                    provisionNewAsset(name)
                    setShowProvisionModal(false)
                  }}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg"
                >
                  Connect & Start Learning
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="h-8"></div>
      </div>
    </div>
  )
}
