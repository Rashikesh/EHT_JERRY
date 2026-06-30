// src/app/components/ResizableChart.tsx
'use client'

import { useState, useRef, useCallback, useEffect, CSSProperties } from 'react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ReferenceLine, Brush 
} from 'recharts'
import { useLayout } from '@/contexts/LayoutContext'

interface ResizableChartProps {
  data: { time: string; gas: number }[]
  events: { time: string; type: string }[]
  riskScore: number
  riskColor: string
}

export default function ResizableChart({ data, events, riskScore, riskColor }: ResizableChartProps) {
  const { chartHeight, setChartHeight } = useLayout()
  const [width, setWidth] = useState<number | string>('100%')
  const [isResizing, setIsResizing] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const startPos = useRef({ x: 0, y: 0, width: 0, height: 0 })
  const currentHandle = useRef<string>('')

  const handleDoubleClick = () => setIsFullscreen(!isFullscreen)

  const handleMouseDown = useCallback((e: React.MouseEvent, handle: string) => {
    e.preventDefault(); e.stopPropagation();
    setIsResizing(true); currentHandle.current = handle;
    startPos.current = { x: e.clientX, y: e.clientY, width: containerRef.current?.offsetWidth || 0, height: containerRef.current?.offsetHeight || 0 };
    document.body.style.cursor = getComputedStyle(e.currentTarget as Element).cursor;
    document.body.style.userSelect = 'none';
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !containerRef.current) return;
    const deltaX = e.clientX - startPos.current.x; const deltaY = e.clientY - startPos.current.y;
    const handle = currentHandle.current;
    let newWidth = startPos.current.width; let newHeight = startPos.current.height;
    if (handle.includes('e')) newWidth = startPos.current.width + deltaX;
    if (handle.includes('w')) newWidth = startPos.current.width - deltaX;
    if (handle.includes('s')) newHeight = startPos.current.height + deltaY;
    if (handle.includes('n')) newHeight = startPos.current.height - deltaY;
    newWidth = Math.max(400, Math.min(newWidth, window.innerWidth - 100));
    newHeight = Math.max(250, Math.min(newHeight, 600));
    setWidth(handle.includes('e') || handle.includes('w') ? newWidth : '100%');
    setChartHeight(newHeight);
  }, [isResizing, setChartHeight])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false); document.body.style.cursor = ''; document.body.style.userSelect = ''; currentHandle.current = '';
  }, [])

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove); window.addEventListener('mouseup', handleMouseUp);
      return () => { window.removeEventListener('mousemove', handleMouseMove); window.removeEventListener('mouseup', handleMouseUp); }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  const containerStyle: CSSProperties = isFullscreen 
    ? { position: 'fixed', top: '5%', left: '5%', width: '90vw', height: '90vh', zIndex: 1000 } 
    : { width: typeof width === 'number' ? `${width}px` : width, height: `${chartHeight}px` };

  return (
    <>
      {isFullscreen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[999]" onClick={() => setIsFullscreen(false)} />
      )}

      <div 
        ref={containerRef}
        onDoubleClick={handleDoubleClick}
        className={`resizable-container glass-card ${isResizing ? 'resizing' : ''} ${isFullscreen ? 'fullscreen-chart' : ''}`}
        style={containerStyle}
      >
        {!isFullscreen && (
          <>
            <div className="resize-handle resize-handle-nw" onMouseDown={(e) => handleMouseDown(e, 'nw')} />
            <div className="resize-handle resize-handle-ne" onMouseDown={(e) => handleMouseDown(e, 'ne')} />
            <div className="resize-handle resize-handle-sw" onMouseDown={(e) => handleMouseDown(e, 'sw')} />
            <div className="resize-handle resize-handle-se" onMouseDown={(e) => handleMouseDown(e, 'se')} />
            <div className="resize-handle resize-handle-n" onMouseDown={(e) => handleMouseDown(e, 'n')} />
            <div className="resize-handle resize-handle-s" onMouseDown={(e) => handleMouseDown(e, 's')} />
            <div className="resize-handle resize-handle-e" onMouseDown={(e) => handleMouseDown(e, 'e')} />
            <div className="resize-handle resize-handle-w" onMouseDown={(e) => handleMouseDown(e, 'w')} />
          </>
        )}

        {/* Chart Content with Risk Score on Right */}
        <div className="h-full flex">
          {/* Left: Chart (75% width) */}
          <div className="flex-1 p-4 flex flex-col">
            <div className="flex justify-between items-center mb-2">
              <h3 className="stat-label flex items-center gap-2">
                📈 Live Telemetry Trend
                {isFullscreen && <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded ml-2">FOCUS MODE</span>}
              </h3>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500">Double-click to {isFullscreen ? 'minimize' : 'expand'}</span>
              </div>
            </div>
            
            <div className="chart-container flex-1" style={{ minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} label={{ value: 'Gas %', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                  
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                  />

                  <ReferenceLine y={40} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'DANGER (40%)', fill: '#ef4444', fontSize: 12, position: 'right' }} />

                  {events.map((event, index) => (
                    <ReferenceLine 
                      key={index} 
                      x={event.time} 
                      stroke={event.type === 'PERMIT BLOCKED' ? '#ef4444' : '#22c55e'} 
                      strokeDasharray="5 5"
                      label={{ 
                        value: event.type, 
                        fill: event.type === 'PERMIT BLOCKED' ? '#ef4444' : '#22c55e', 
                        fontSize: 10, 
                        position: 'top' 
                      }} 
                    />
                  ))}

                  <Line type="monotone" dataKey="gas" name="Gas %" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981' }} />
                  
                  <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#0f172a" travellerWidth={8} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right: AI Risk Score Panel (25% width) */}
          <div className="w-64 border-l border-gray-700 p-4 flex flex-col justify-center bg-black/20">
            <div className="text-center">
              <h3 className="stat-label mb-2 text-xs uppercase">AI Risk Score</h3>
              <div className={`text-6xl font-black text-${riskColor}-500 mb-2`}>
                {riskScore}
                <span className="text-2xl text-slate-500">/100</span>
              </div>
              <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                riskScore > 70 ? 'bg-red-500/20 text-red-400' : 
                riskScore > 40 ? 'bg-yellow-500/20 text-yellow-400' : 
                'bg-green-500/20 text-green-400'
              }`}>
                {riskScore > 70 ? '🚨 Critical' : riskScore > 40 ? '⚠️ Elevated' : '✅ Normal'}
              </div>
            </div>
            
            {/* Mini Stats */}
            <div className="mt-6 space-y-3">
              <div className="bg-black/30 p-2 rounded text-center">
                <p className="text-[10px] text-slate-500 uppercase">Status</p>
                <p className="text-sm font-bold text-white">{riskScore < 40 ? 'Safe' : riskScore < 70 ? 'Warning' : 'Danger'}</p>
              </div>
              <div className="bg-black/30 p-2 rounded text-center">
                <p className="text-[10px] text-slate-500 uppercase">Trend</p>
                <p className="text-sm font-bold text-blue-400">Real-time</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}