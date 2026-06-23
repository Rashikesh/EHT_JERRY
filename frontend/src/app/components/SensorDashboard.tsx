// src/components/SensorDashboard.tsx
'use client'

import { useEffect, useState } from 'react'
import PlantMap from './PlantMap'

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
    gas: 0, 
    pressure: 0, 
    temperature: 0, 
    shift: 0,
    permit_active: true,
    ai_justification: '',
    blocked_reason: null
  })
  const [status, setStatus] = useState('Connecting to backend...')
  
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
       console.log('📩 Received from backend:', parsed)  
      setData(prev => ({ ...prev, ...parsed }))
    }
    ws.onclose = () => setStatus('Disconnected')
    ws.onerror = () => setStatus('Connection Error')

    // ✅ FIXED: Proper closing braces
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className={`p-3 rounded-lg text-center font-bold ${status === 'Connected to PLC' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
        Backend Status: {status}
      </div>

      {/* Sensor Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Gas Level */}
        <div className={`p-6 rounded-xl shadow-lg border-2 ${data.gas > 40 ? 'bg-red-950 border-red-500 animate-pulse' : 'bg-gray-800 border-gray-700'}`}>
          <h3 className="text-gray-400 text-sm uppercase">Gas Level</h3>
          <p className="text-4xl font-bold mt-2">{data.gas}%</p>
          {data.gas > 40 && <p className="text-red-400 font-bold mt-2">⚠️ CRITICAL DANGER</p>}
        </div>

        {/* Pressure */}
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm uppercase">Pressure</h3>
          <p className="text-4xl font-bold mt-2">{data.pressure} <span className="text-lg">bar</span></p>
        </div>

        {/* Temperature */}
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm uppercase">Temperature</h3>
          <p className="text-4xl font-bold mt-2">{data.temperature}°C</p>
        </div>
      </div>

      {/* Digital Permit Interlock Status */}
      <div className={`p-8 rounded-xl text-center border-2 ${!data.permit_active ? 'bg-red-900/30 border-red-600' : 'bg-green-900/30 border-green-600'}`}>
        <h2 className="text-2xl font-bold mb-2">Digital Permit Intelligence Agent</h2>
        <p className="text-4xl font-black mt-4">
          {data.permit_active ? '🟢 PERMIT ACTIVE (Safe to Work)' : '🔴 PERMIT BLOCKED (PLC Interlock Triggered)'}
        </p>
        
        {/* AI Justification Box */}
        {data.ai_justification && (
          <div className="mt-6 p-4 bg-black/40 rounded-lg text-left border border-gray-600">
            <h3 className="text-yellow-400 font-bold mb-2">🧠 AI Safety Justification (RAG):</h3>
            <p className="text-gray-300 text-sm whitespace-pre-wrap">{data.ai_justification}</p>
          </div>
        )}

        {/* Confidence Score Section */}
        {!data.permit_active && data.confidence && (
          <div className="mt-4 p-4 bg-yellow-900/20 rounded-lg border border-yellow-600/50 text-left">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-yellow-400 font-bold">🎯 AI Confidence Level</h3>
              <span className="text-2xl font-black text-yellow-400">{data.confidence}%</span>
            </div>
            
            <div className="w-full bg-gray-700 rounded-full h-2.5 mb-3">
              <div 
                className="bg-yellow-500 h-2.5 rounded-full transition-all duration-500" 
                style={{ width: `${data.confidence}%` }}
              ></div>
            </div>

            <h4 className="text-gray-400 text-xs uppercase font-bold mb-1">Triggered Factors:</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              {data.all_reasons?.map((reason: string, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span> {reason}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Live Plant Map */}
      <div className="mt-6">
        <h3 className="text-gray-400 text-sm uppercase font-bold mb-3">Live Plant Telemetry</h3>
        <PlantMap isDanger={!data.permit_active} gasLevel={data.gas} />
      </div>
      
      {/* AI Risk Score */}
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <h3 className="text-gray-400 text-sm uppercase">AI Risk Score</h3>
        <p className={`text-5xl font-black mt-2 text-${riskColor}-500`}>
          {riskScore}/100
        </p>
        <p className="text-gray-500 text-xs mt-2">
          {riskScore > 70 ? '🚨 CRITICAL' : riskScore > 40 ? '⚠️ ELEVATED' : '✅ NORMAL'}
        </p>
      </div>
    </div>
  )
}