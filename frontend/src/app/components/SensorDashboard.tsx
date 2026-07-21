"use client"

import { useEffect, useState, useRef } from "react"
import ResizableChart from "./ResizableChart"
import { useLayout } from "@/contexts/LayoutContext"
import "@/styles/dashboard.css"
import MissionControl from "@/app/components/dashboard/MissionControl"
import ConnectionStatus from "./dashboard/ConnectionStatus"
import DashboardHeader from "./dashboard/DashboardHeader"
import ControlButtons from "./dashboard/ControlButtons"
import SensorGrid from "./dashboard/SensorGrid"
import PermitStatusPanel from "./dashboard/PermitStatusPanel"
import DigitalTwin3D from "./DigitalTwin3D"
import AuditChainPanel from "./AuditChainPanel"
import TimelinePanel from "./TimelinePanel"

// --- Interfaces ---
interface IoTAsset {
  id: string
  name: string
  lat: number
  lng: number
  status: "learning" | "active" | "critical"
  gasLevel: number
  learnedThreshold: number
}

interface Prediction {
  type: string
  current: number
  threshold: number
  trend: number
  minutes_to_breach: number
  severity: "warning" | "critical"
}

interface SimilarIncident {
  id: string
  date: string
  gas_level: number
  pressure: number
  temp: number
  cause: string
  outcome: string
  lessons: string
  similarity_score: number
}

interface ShiftAnalysis {
  fatigue_multiplier: number
  risk_level: "low" | "medium" | "high"
  factors: { night_shift: boolean; overtime: boolean; hours_worked: number }
}

interface SensorData {
  gas: number
  pressure: number
  temperature: number
  shift: string
  permit_active: boolean
  ai_justification: string
  blocked_reason: string | null
  confidence?: number
  anomaly_score?: number
  ml_confidence?: number
  ml_status?: string
  predictions?: Prediction[]
  trends?: { gas: number; pressure: number; temperature: number }
  shift_analysis?: ShiftAnalysis
  similar_incidents?: SimilarIncident[]
}

interface TimelineEvent {
  time: string
  event: string
  detail: string
  type: "PERMIT" | "SHIFT" | "BLOCK" | "INFO"
}

export default function SensorDashboard() {
  // Prefix unused vars with '_' to satisfy ESLint while preserving the code
  useLayout()

  // ✅ FIX 1: Replaced 'any' with proper TimelineEvent interface
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([])
  const alarmSound = useRef<HTMLAudioElement | null>(null)

  const [data, setData] = useState<SensorData>({
    gas: 0,
    pressure: 0,
    temperature: 0,
    shift: "Day Shift",
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
  const [showGodMode, setShowGodMode] = useState(false)

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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

  // ✅ FIX 2: Prefixed unused state setters with '_'
  // const [_showProvisionModal, _setShowProvisionModal] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_showProvisionModal, _setShowProvisionModal] = useState(false)
  const [lastHardwareCommand, setLastHardwareCommand] = useState<string | null>(
    null,
  )

  useEffect(() => {
    alarmSound.current = new Audio(
      "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3",
    )
    if (alarmSound.current) alarmSound.current.volume = 0.3
  }, [])

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

  const triggerBackendAction = async (endpoint: string) => {
    try {
      await fetch(`http://localhost:8000${endpoint}`, { method: "POST" })
    } catch (error) {
      console.error("Action failed:", error)
    }
  }

  // ✅ FIX 3: Prefixed unused function with '_'
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _provisionNewAsset = async (
    name: string,
    protocol: string = "simulated",
  ) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/provision-asset",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            protocol,
            lat: 28.6139 + (Math.random() * 0.002 - 0.001),
            lng: 77.209 + (Math.random() * 0.002 - 0.001),
          }),
        },
      )
      const result = await response.json()
      setAssets((prev) => [...prev, result.asset])
    } catch (error) {
      console.error("❌ Failed to provision asset:", error)
    }
  }

  // ✅ FIX 4: Moved scrollToMap and scrollToTop ABOVE the useEffect that uses them
  const scrollToMap = () =>
    document
      .getElementById("map-section")
      ?.scrollIntoView({ behavior: "smooth", block: "start" })

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" })

  useEffect(() => {
    let ws: WebSocket
    let reconnectTimeout: ReturnType<typeof setTimeout>
    let pingInterval: ReturnType<typeof setInterval>
    let isUnmounted = false

    const connect = () => {
      ws = new WebSocket(
        process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws",
      )

      ws.onopen = () => {
        setStatus("Connected to PLC")
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }))
          }
        }, 25000)
      }

      ws.onmessage = (event) => {
        const parsed = JSON.parse(event.data)
        const now = new Date().toLocaleTimeString()

        if (parsed.timeline_events) {
          setTimelineEvents(parsed.timeline_events)
        }

        setData((prev) => {
          if (
            prev.permit_active &&
            !parsed.permit_active &&
            alarmSound.current
          ) {
            alarmSound.current
              .play()
              .catch(() => console.log("Audio requires user interaction"))
          }

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

      ws.onclose = () => {
        setStatus("Disconnected")
        clearInterval(pingInterval)
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connect, 3000)
        }
      }

      // ✅ FIX 5: Removed unused 'e' parameter
      ws.onerror = () => {
        setStatus("Connection Error")
      }
    }

    connect()

    return () => {
      isUnmounted = true
      clearTimeout(reconnectTimeout)
      clearInterval(pingInterval)
      if (
        ws &&
        (ws.readyState === WebSocket.OPEN ||
          ws.readyState === WebSocket.CONNECTING)
      ) {
        ws.close()
      }
    }
  }, [])

  // KEYBOARD SHORTCUTS
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return
      if (e.key.toLowerCase() === "e") triggerBackendAction("/force-emergency")
      if (e.key.toLowerCase() === "r") triggerBackendAction("/reset-sensors")
      if (e.key.toLowerCase() === "m") scrollToMap()
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="dashboard-wrapper">
      <div className="w-full h-full space-y-6 flex flex-col pb-8">
        <ConnectionStatus status={status} />
        <DashboardHeader />

        {/* Navigation & Shortcuts Hint */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex gap-3">
            <button
              onClick={scrollToMap}
              className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-400 text-xs font-bold rounded-lg transition-all flex items-center gap-2"
            >
              <span>📍</span> Jump to Map
            </button>
            <button
              onClick={scrollToTop}
              className="px-4 py-2 bg-slate-700/20 hover:bg-slate-700/30 border border-slate-500/30 text-slate-400 text-xs font-bold rounded-lg transition-all flex items-center gap-2"
            >
              <span>↑</span> Back to Top
            </button>
          </div>

          <div className="hidden md:flex items-center gap-2 text-[10px] text-slate-500 font-mono bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700/50">
            <span className="text-blue-400 font-bold">[E]</span> Emergency
            <span className="text-slate-700">|</span>
            <span className="text-green-400 font-bold">[R]</span> Reset
            <span className="text-slate-700">|</span>
            <span className="text-yellow-400 font-bold">[M]</span> Map
          </div>
        </div>

        {lastHardwareCommand && (
          <div className="w-full bg-red-900/30 border border-red-500/50 rounded-lg p-3 mb-4 flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚙️</span>
              <div>
                <p className="text-red-400 text-xs font-bold uppercase">
                  Last Hardware Command
                </p>
                <p className="text-white font-mono text-sm">
                  {lastHardwareCommand}
                </p>
              </div>
            </div>
            <button
              onClick={() => setLastHardwareCommand(null)}
              className="text-slate-400 hover:text-white text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Predictive Alerts */}
        {data.predictions && data.predictions.length > 0 && (
          <div className="glass-card p-5 mb-4 border-2 border-yellow-500/50 animate-pulse">
            <h3 className="text-yellow-400 font-bold text-sm mb-3 flex items-center gap-2">
              <span className="text-xl">⚠️</span> PREDICTIVE ALERTS - BREACH
              IMMINENT
            </h3>
            <div className="space-y-2">
              {data.predictions.map((pred, idx) => (
                <div
                  key={idx}
                  className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-white font-bold text-sm">
                      {pred.type.replace("_", " ").toUpperCase()}
                    </span>
                    <span
                      className={`text-xs font-bold px-2 py-1 rounded ${pred.severity === "critical" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"}`}
                    >
                      {pred.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs">
                    Current:{" "}
                    <span className="text-white font-bold">{pred.current}</span>{" "}
                    → Threshold:{" "}
                    <span className="text-red-400 font-bold">
                      {pred.threshold}
                    </span>{" "}
                    in ~
                    <span className="text-yellow-400 font-bold">
                      {pred.minutes_to_breach}
                    </span>{" "}
                    mins
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Shift Fatigue */}
        {data.shift_analysis && (
          <div
            className={`glass-card p-4 mb-4 border ${data.shift_analysis.risk_level === "high" ? "border-orange-500/50 bg-orange-900/10" : "border-green-500/50 bg-green-900/10"}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🌙</span>
                <div>
                  <p className="text-white font-bold text-sm">
                    Shift Fatigue Analysis
                  </p>
                  <p className="text-slate-400 text-xs">
                    {data.shift_analysis.factors.night_shift &&
                      "Night Shift • "}
                    {data.shift_analysis.factors.hours_worked}h worked
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p
                  className={`text-2xl font-black ${data.shift_analysis.risk_level === "high" ? "text-orange-400" : "text-green-400"}`}
                >
                  {data.shift_analysis.fatigue_multiplier.toFixed(1)}x
                </p>
                <p className="text-slate-400 text-xs uppercase">
                  Risk Multiplier
                </p>
              </div>
            </div>
          </div>
        )}

        <ControlButtons />
        <SensorGrid
          gas={data.gas}
          pressure={data.pressure}
          temperature={data.temperature}
        />

        <div className="mb-6 h-[400px] w-full">
          <ResizableChart
            data={chartData}
            events={systemEvents}
            riskScore={riskScore}
            riskColor={riskColor}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
          <div className="lg:col-span-2">
            <MissionControl />
          </div>
          <div className="lg:col-span-3">
            <PermitStatusPanel
              permitActive={data.permit_active}
              aiJustification={data.ai_justification}
              confidence={data.ml_confidence || data.confidence}
              gas={data.gas}
              pressure={data.pressure}
              temperature={data.temperature}
              anomalyScore={data.anomaly_score}
              similarIncidents={data.similar_incidents}
            />
          </div>
        </div>

        {/* ✅ FIX 6: Cleaned up the mangled JSX into a perfect 3-column grid */}
        <div className="p-6 mb-8 relative">
          <div id="map-section" className="w-full scroll-mt-4 mb-6">
            <h3 className="stat-label text-lg font-bold text-white flex items-center gap-2">
              <span>📍</span> Live Plant Telemetry & Digital Twin
            </h3>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 3D Twin */}
            <div className="glass-card p-6 lg:col-span-1">
              <h3 className="stat-label text-sm font-bold text-white mb-4 uppercase tracking-wider">
                📍 3D Digital Twin
              </h3>
              <DigitalTwin3D
                gasLevel={data.gas}
                isDanger={!data.permit_active}
              />
            </div>

            {/* Timeline */}
            <div className="lg:col-span-1">
              <TimelinePanel events={timelineEvents} />
            </div>

            {/* Audit Chain */}
            <div className="lg:col-span-1">
              <AuditChainPanel />
            </div>
          </div>
        </div>

        {/* Provisioning Modal */}
        {_showProvisionModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[1000] flex items-center justify-center p-4">
            {/* Modal Content */}
          </div>
        )}

        {/* GOD MODE: Floating Simulation Panel */}
        <button
          onClick={() => setShowGodMode(!showGodMode)}
          className="fixed bottom-6 left-6 z-50 bg-slate-900/90 hover:bg-slate-800 text-slate-400 hover:text-white p-3 rounded-full backdrop-blur-md border border-slate-700 shadow-xl transition-all hover:scale-110"
          title="Simulation Controls"
        >
          🎮
        </button>

        {showGodMode && (
          <div className="fixed bottom-20 left-6 z-50 bg-slate-950/95 border border-slate-700 p-4 rounded-xl backdrop-blur-xl shadow-2xl w-64 animate-in fade-in slide-in-from-bottom-4">
            <h4 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
              <span>🎮</span> Demo Controls
            </h4>
            <div className="space-y-2">
              <button
                onClick={() => triggerBackendAction("/force-emergency")}
                className="w-full bg-red-600/20 hover:bg-red-600/40 text-red-400 text-xs py-2 rounded border border-red-500/30 transition-all"
              >
                🚨 Trigger Gas Leak
              </button>
              <button
                onClick={() => triggerBackendAction("/reset-sensors")}
                className="w-full bg-green-600/20 hover:bg-green-600/40 text-green-400 text-xs py-2 rounded border border-green-500/30 transition-all"
              >
                ✅ Reset System
              </button>
              <button
                onClick={() => triggerBackendAction("/api/simulate-cctv")}
                className="w-full bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 text-xs py-2 rounded border border-blue-500/30 transition-all"
              >
                📷 Trigger CCTV Alert
              </button>
            </div>
          </div>
        )}

        <div className="h-8"></div>
      </div>
    </div>
  )
}
