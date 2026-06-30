// src/app/components/dashboard/MissionControl.tsx
"use client"

import { useState } from "react"

export default function MissionControl() {
  const [isSystemActive, setIsSystemActive] = useState(false)
  const [lastAction, setLastAction] = useState("System Idle")
  const [isDownloading, setIsDownloading] = useState(false)

  const handleAction = async (
    action: string,
    endpoint: string,
    method = "POST",
  ) => {
    setLastAction(`Executing: ${action}...`)
    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, { method })
      if (res.ok) {
        setLastAction(`✅ ${action} Successful`)
        if (action === "Initialize System") setIsSystemActive(true)
      } else {
        setLastAction(`❌ ${action} Failed (Check Backend)`)
      }
    } catch (error) {
      setLastAction(`❌ Connection Error: Is backend running?`)
    }
  }

  const handleDownloadPDF = async () => {
    setIsDownloading(true)
    setLastAction("Generating Compliance PDF...")
    try {
      const res = await fetch("http://localhost:8000/download-report")
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = "OSHA_Compliance_Report.pdf"
        document.body.appendChild(a)
        a.click()
        a.remove()
        setLastAction("✅ PDF Downloaded Successfully")
      }
    } catch (error) {
      setLastAction("❌ PDF Generation Failed")
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="relative p-6 rounded-2xl border border-blue-500/30 bg-gradient-to-br from-slate-900/60 via-blue-950/40 to-slate-900/60 backdrop-blur-2xl overflow-hidden shadow-2xl">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-pulse" />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)`,
          backgroundSize: "50px 50px",
        }}
      />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-black text-white flex items-center gap-3">
              <span className="text-3xl animate-bounce">🚀</span>
              <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent drop-shadow-lg">
                Mission Control
              </span>
            </h2>
            <p className="text-slate-400 text-sm mt-1 font-medium tracking-wide">
              Unified Demo Orchestration
            </p>
          </div>
          <div
            className={`px-4 py-2 rounded-full text-xs font-bold border-2 transition-all duration-300 ${
              isSystemActive
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/60 shadow-[0_0_20px_rgba(16,185,129,0.5)]"
                : "bg-slate-700/50 text-slate-400 border-slate-600"
            }`}
          >
            <span className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${isSystemActive ? "bg-emerald-400 animate-ping" : "bg-slate-400"}`}
              />
              {isSystemActive ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}
            </span>
          </div>
        </div>

        {/* Enhanced Status Indicator */}
        <div className="relative bg-black/60 rounded-xl p-4 mb-6 border border-white/10 overflow-hidden shadow-inner">
          <div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full"
            style={{
              animation: "shimmer 2s infinite",
            }}
          />
          <p className="text-[10px] text-slate-500 uppercase font-bold mb-2 tracking-widest">
            Live Action Log
          </p>
          <p
            className={`text-sm font-mono font-bold transition-colors duration-300 ${
              lastAction.includes("❌")
                ? "text-red-400"
                : lastAction.includes("✅")
                  ? "text-emerald-400"
                  : "text-cyan-400"
            }`}
          >
            {lastAction}
          </p>
        </div>

        {/* Enhanced Button Grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* Initialize System */}
          <button
            onClick={() => handleAction("Initialize System", "/reset-sensors")}
            className="group relative px-4 py-3 bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-blue-500/40 hover:scale-[1.03] active:scale-[0.97] border border-blue-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                🟢
              </span>
              <span className="drop-shadow-lg">Initialize</span>
            </div>
          </button>

          {/* Trigger Emergency */}
          <button
            onClick={() =>
              handleAction("Trigger Emergency", "/force-emergency")
            }
            className="group relative px-4 py-3 bg-gradient-to-br from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-red-500/40 hover:scale-[1.03] active:scale-[0.97] border border-red-400/30 overflow-hidden animate-pulse"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                🚨
              </span>
              <span className="drop-shadow-lg">Emergency</span>
            </div>
          </button>

          {/* Reset to Normal */}
          <button
            onClick={() => handleAction("Reset to Normal", "/reset-sensors")}
            className="group relative px-4 py-3 bg-gradient-to-br from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-slate-500/40 hover:scale-[1.03] active:scale-[0.97] border border-slate-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                🔄
              </span>
              <span className="drop-shadow-lg">Reset</span>
            </div>
          </button>

          {/* Download Audit PDF */}
          <button
            onClick={handleDownloadPDF}
            disabled={isDownloading}
            className="group relative px-4 py-3 bg-gradient-to-br from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-purple-500/40 hover:scale-[1.03] active:scale-[0.97] border border-purple-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                {isDownloading ? "⏳" : "📄"}
              </span>
              <span className="drop-shadow-lg">
                {isDownloading ? "Generating..." : "PDF"}
              </span>
            </div>
          </button>

          {/* Test Modbus PLC */}
          <button
            onClick={() => handleAction("Test Modbus PLC", "/api/test-modbus")}
            className="group relative px-4 py-3 bg-gradient-to-br from-orange-600 to-orange-700 hover:from-orange-500 hover:to-orange-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-orange-500/40 hover:scale-[1.03] active:scale-[0.97] border border-orange-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                ⚙️
              </span>
              <span className="drop-shadow-lg">Modbus</span>
            </div>
          </button>

          {/* Test OPC UA SCADA */}
          <button
            onClick={() => handleAction("Test OPC UA SCADA", "/api/test-opcua")}
            className="group relative px-4 py-3 bg-gradient-to-br from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-indigo-500/40 hover:scale-[1.03] active:scale-[0.97] border border-indigo-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                🏭
              </span>
              <span className="drop-shadow-lg">OPC UA</span>
            </div>
          </button>

          {/* Simulate CCTV Alert */}
          <button
            onClick={() =>
              handleAction("Simulate CCTV Smoke", "/api/simulate-cctv")
            }
            className="group relative px-4 py-3 bg-gradient-to-br from-pink-600 to-pink-700 hover:from-pink-500 hover:to-pink-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-pink-500/40 hover:scale-[1.03] active:scale-[0.97] border border-pink-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                📷
              </span>
              <span className="drop-shadow-lg">CCTV</span>
            </div>
          </button>

          {/* Simulate Night Shift */}
          <button
            onClick={() =>
              handleAction("Switch to Night Shift", "/api/simulate-shift")
            }
            className="group relative px-4 py-3 bg-gradient-to-br from-teal-600 to-teal-700 hover:from-teal-500 hover:to-teal-600 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg hover:shadow-teal-500/40 hover:scale-[1.03] active:scale-[0.97] border border-teal-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            <div className="relative flex items-center justify-center gap-2">
              <span className="text-xl group-hover:scale-125 transition-transform duration-300">
                🌙
              </span>
              <span className="drop-shadow-lg">Night Shift</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}
