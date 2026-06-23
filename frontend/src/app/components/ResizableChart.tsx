// src/components/ResizableChart.tsx
'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface ResizableChartProps {
  data: { time: string; gas: number }[]
}

interface Dimensions {
  width: number | string
  height: number
}

export default function ResizableChart({ data }: ResizableChartProps) {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: '100%', height: 300 })
  const [isResizing, setIsResizing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const startPos = useRef({ x: 0, y: 0, width: 0, height: 0 })
  const currentHandle = useRef<string>('')

  const handleMouseDown = useCallback((e: React.MouseEvent, handle: string) => {
    e.preventDefault()
    e.stopPropagation()
    
    setIsResizing(true)
    currentHandle.current = handle
    startPos.current = {
      x: e.clientX,
      y: e.clientY,
      width: containerRef.current?.offsetWidth || 0,
      height: containerRef.current?.offsetHeight || 0
    }
    
    document.body.style.cursor = getComputedStyle(e.currentTarget as Element).cursor
    document.body.style.userSelect = 'none'
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !containerRef.current) return

    const deltaX = e.clientX - startPos.current.x
    const deltaY = e.clientY - startPos.current.y
    const handle = currentHandle.current

    let newWidth = startPos.current.width
    let newHeight = startPos.current.height

    // Calculate new dimensions based on handle
    if (handle.includes('e')) newWidth = startPos.current.width + deltaX
    if (handle.includes('w')) newWidth = startPos.current.width - deltaX
    if (handle.includes('s')) newHeight = startPos.current.height + deltaY
    if (handle.includes('n')) newHeight = startPos.current.height - deltaY

    // Apply constraints
    newWidth = Math.max(400, Math.min(newWidth, window.innerWidth - 100))
    newHeight = Math.max(200, Math.min(newHeight, 600))

    setDimensions({ 
      width: handle.includes('e') || handle.includes('w') ? newWidth : '100%',
      height: newHeight
    })
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    currentHandle.current = ''
  }, [])

  // Attach global event listeners
  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  return (
    <div 
      ref={containerRef}
      className={`resizable-container glass-card ${isResizing ? 'resizing' : ''}`}
      style={{ 
        width: typeof dimensions.width === 'number' ? `${dimensions.width}px` : dimensions.width,
        height: `${dimensions.height}px`
      }}
    >
      {/* Resize Handles */}
      <div className="resize-handle resize-handle-nw" onMouseDown={(e) => handleMouseDown(e, 'nw')} />
      <div className="resize-handle resize-handle-ne" onMouseDown={(e) => handleMouseDown(e, 'ne')} />
      <div className="resize-handle resize-handle-sw" onMouseDown={(e) => handleMouseDown(e, 'sw')} />
      <div className="resize-handle resize-handle-se" onMouseDown={(e) => handleMouseDown(e, 'se')} />
      <div className="resize-handle resize-handle-n" onMouseDown={(e) => handleMouseDown(e, 'n')} />
      <div className="resize-handle resize-handle-s" onMouseDown={(e) => handleMouseDown(e, 's')} />
      <div className="resize-handle resize-handle-e" onMouseDown={(e) => handleMouseDown(e, 'e')} />
      <div className="resize-handle resize-handle-w" onMouseDown={(e) => handleMouseDown(e, 'w')} />

      {/* Chart Content */}
      <div className="h-full p-4">
        <h3 className="stat-label mb-4 flex justify-between items-center">
          <span>📈 Live Telemetry Trend</span>
          <span className="text-xs text-slate-500">
            {typeof dimensions.width === 'number' ? `${Math.round(dimensions.width)}px` : 'Auto'} × {dimensions.height}px
          </span>
        </h3>
        <div className="chart-container" style={{ height: 'calc(100% - 30px)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
              <YAxis stroke="#94a3b8" fontSize={10} domain={[0, 100]} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#f8fafc'
                }}
              />
              <ReferenceLine 
                y={40} 
                stroke="#ef4444" 
                strokeDasharray="3 3" 
                label={{ value: 'DANGER', fill: '#ef4444', fontSize: 10 }} 
              />
              <Line 
                type="monotone" 
                dataKey="gas" 
                name="Gas %" 
                stroke="#10b981" 
                strokeWidth={3} 
                dot={false} 
                activeDot={{ r: 6, fill: '#10b981' }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}