// src/app/page.tsx
'use client'

import dynamic from 'next/dynamic'

// Dynamically import the dashboard with SSR disabled
// This fixes the "window is not defined" error for Leaflet maps
const SensorDashboard = dynamic(() => import('@/app/components/SensorDashboard'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p>Loading Industrial Safety Monitor...</p>
      </div>
    </div>
  )
})

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white p-6 font-sans">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-blue-500 tracking-tight">Industrial Safety Monitor</h1>
            <p className="text-gray-500 text-sm mt-1">Digital Permit Intelligence Agent v1.0</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500 uppercase">System Status</p>
            <p className="text-green-400 font-bold flex items-center justify-end gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> ONLINE
            </p>
          </div>
        </div>

        {/* Main Content */}
        <SensorDashboard />
      </div>
    </main>
  )
}