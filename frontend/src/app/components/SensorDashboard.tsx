// src/components/SensorDashboard.tsx
'use client'

import { useEffect, useState } from 'react'
import PlantMap from './PlantMap'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts'
import '@/styles/dashboard.css' // 👈 Import the new CSS
import '@/app/components/ResizableChart'
import ResizableChart from '@/app/components/ResizableChart'

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
  const [data, setData] = useState<SensorData>({ 
    gas: 0, pressure: 0, temperature: 0, shift: 0,
    permit_active: true, ai_justification: '', blocked_reason: null
  })
  const [status, setStatus] = useState('Connecting to backend...')
  const [chartData, setChartData] = useState<{ time: string, gas: number }[]>([])

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
  const riskColor = riskScore > 70 ? 'red' : riskScore > 40 ? 'yellow' : 'green'
 
  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws')

    ws.onopen = () => setStatus('Connected to PLC')
    ws.onmessage = (event) => {
      const parsed = JSON.parse(event.data)
      setData(prev => ({ ...prev, ...parsed }))
      
      const now = new Date().toLocaleTimeString()
      setChartData(prev => {
        const newData = [...prev, { time: now, gas: parsed.gas }]
        return newData.length > 30 ? newData.slice(-30) : newData
      })
    }
    ws.onclose = () => setStatus('Disconnected')
    ws.onerror = () => setStatus('Connection Error')

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
  }, [])

  return (
    <div className="dashboard-wrapper">
      <div className="w-full h-full space-y-6 flex flex-col">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Industrial Safety Monitor</h1>
            <p className="text-slate-400 text-sm mt-1">Digital Permit Intelligence Agent v1.0</p>
          </div>
          <div className={`px-4 py-2 rounded-full text-sm font-bold ${status === 'Connected to PLC' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
            {status === 'Connected to PLC' ? '● ONLINE' : '● OFFLINE'}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex justify-center gap-4 mb-8">
          <button 
            onClick={() => fetch('http://localhost:8000/force-emergency', { method: 'POST' })}
            className="action-btn emergency"
          >
            🚨 SIMULATE EMERGENCY
          </button>
          <button 
            onClick={() => fetch('http://localhost:8000/reset-sensors', { method: 'POST' })}
            className="action-btn reset"
          >
            🔄 Reset to Normal
          </button>
        </div>

        {/* Sensor Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className={`glass-card p-6 stat-box ${data.gas > 40 ? 'border-red-500/50' : ''}`}>
            <h3 className="stat-label">Gas Level</h3>
            <p className={`stat-value ${data.gas > 40 ? 'danger' : ''}`}>{data.gas}%</p>
            {data.gas > 40 && <p className="text-red-400 font-bold mt-2 text-sm">⚠️ CRITICAL DANGER</p>}
          </div>
          <div className="glass-card p-6 stat-box">
            <h3 className="stat-label">Pressure</h3>
            <p className="stat-value">{data.pressure} <span className="text-lg text-slate-400">bar</span></p>
          </div>
          <div className="glass-card p-6 stat-box">
            <h3 className="stat-label">Temperature</h3>
            <p className="stat-value">{data.temperature}°C</p>
          </div>
        </div>

        {/* Live Chart */}
        {/* <div className="glass-card p-6">
          <h3 className="stat-label mb-4">📈 Live Telemetry Trend</h3>
          <div className="chart-container" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={10} />
                <Tooltip />
                <ReferenceLine y={40} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'DANGER THRESHOLD', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="gas" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div> */}

          <ResizableChart data = {chartData}/>

        {/* Permit Status */}
        {/* 📐 NEW: 1/3 Left + 2/3 Right Layout */}
        {/* <div className="grid grid-cols-1 lg:grid-cols-3 gap-6"> */}
        {/* 📐 NEW: 1/3 Left + 2/3 Right Layout (Stretches to fill height) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
          
          {/* LEFT COLUMN: Fixed space for Permit Status & AI Justification */}
          <div className="lg:col-span-1">
            <div className={`alert-box ${!data.permit_active ? 'danger' : 'safe'}`}>
              <h2>Digital Permit Intelligence</h2>
              <p className="status-text">
                {data.permit_active ? '🟢 PERMIT ACTIVE' : ' PERMIT BLOCKED'}
              </p>
              <p className="text-slate-400 text-sm mb-4">
                {data.permit_active 
                  ? 'Environmental parameters are within safe limits. Work may proceed.' 
                  : 'PLC Interlock Triggered. All hot work is immediately suspended.'}
              </p>
              
              {/* AI Justification Box */}
              {data.ai_justification && (
                <div className="justification-box">
                  <h3 className="text-yellow-400 font-bold text-xs uppercase mb-2">🧠 AI Safety Justification</h3>
                  <p className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">{data.ai_justification}</p>
                </div>
              )}

              {/* Confidence Score (Only show if blocked) */}
              {!data.permit_active && data.confidence && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>AI Confidence</span>
                    <span className="text-yellow-400 font-bold">{data.confidence}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-1.5">
                    <div className="bg-yellow-500 h-1.5 rounded-full" style={{ width: `${data.confidence}%` }}></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: Map and Risk Score */}
          <div className="lg:col-span-2 space-y-6">
            {/* Live Plant Map */}
            <div className="glass-card p-6">
              <h3 className="stat-label mb-4">📍 Live Plant Telemetry (Zone B)</h3>
              <div style={{ height: '350px', borderRadius: '12px', overflow: 'hidden' }}>
                <PlantMap isDanger={!data.permit_active} gasLevel={data.gas} />
              </div>
            </div>
            
            {/* AI Risk Score */}
            <div className="glass-card p-6 flex justify-between items-center">
              <div>
                <h3 className="stat-label mb-1">AI Risk Score</h3>
                <p className="text-slate-400 text-xs uppercase tracking-wider">
                  {riskScore > 70 ? '🚨 Critical Risk Detected' : riskScore > 40 ? '⚠️ Elevated Risk' : '✅ Normal Operations'}
                </p>
              </div>
              <p className={`text-6xl font-black text-${riskColor}-500`}>{riskScore}<span className="text-2xl text-slate-500">/100</span></p>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}