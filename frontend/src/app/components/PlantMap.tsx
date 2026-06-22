// src/components/PlantMap.tsx
'use client'

import { MapContainer, TileLayer, CircleMarker, Circle, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Fixed coordinates for our "Mock Plant" (You can change these)
const PLANT_CENTER: [number, number] = [28.6139, 77.2090] 

interface PlantMapProps {
  isDanger: boolean
  gasLevel: number
}

export default function PlantMap({ isDanger, gasLevel }: PlantMapProps) {
  return (
    <div className="h-[400px] w-full rounded-xl overflow-hidden border border-gray-700 relative z-0 shadow-2xl">
      <MapContainer 
        center={PLANT_CENTER} 
        zoom={16} 
        scrollWheelZoom={false} 
        style={{ height: '100%', width: '100%' }}
      >
        {/* Dark Matter Tiles for that "Industrial Command Center" look */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Sensor A-1 (The Gas Sensor that is spiking) */}
        <CircleMarker 
          center={PLANT_CENTER} 
          radius={12} 
          color={isDanger ? '#ef4444' : '#22c55e'} 
          fillColor={isDanger ? '#ef4444' : '#22c55e'} 
          fillOpacity={1}
          weight={3}
        >
          <Popup>
            <b>Sensor A-1 (Gas)</b><br />
            Current Level: {gasLevel}%
          </Popup>
        </CircleMarker>

        {/* The "Danger Zone" Radius - Only appears when gas > 40% */}
        {isDanger && (
          <Circle
            center={PLANT_CENTER}
            radius={150} // 150 meters radius
            pathOptions={{ 
              color: '#ef4444', 
              fillColor: '#ef4444', 
              fillOpacity: 0.2, 
              weight: 2,
              className: 'animate-pulse' // Tailwind pulse effect on the SVG
            }}
          />
        )}

        {/* Sensor B-2 (Safe Pressure Sensor nearby) */}
        <CircleMarker 
          center={[PLANT_CENTER[0] + 0.0015, PLANT_CENTER[1] + 0.0015]} 
          radius={10} 
          color="#3b82f6" 
          fillColor="#3b82f6" 
          fillOpacity={0.8}
          weight={2}
        >
          <Popup>Sensor B-2 (Pressure) - Safe</Popup>
        </CircleMarker>

      </MapContainer>
      
      {/* Floating Status Label */}
      <div className="absolute top-4 left-4 bg-black/80 text-white px-3 py-1 rounded text-xs font-bold z-[1000] border border-gray-600 backdrop-blur-sm">
         LIVE PLANT VIEW - ZONE B
      </div>
    </div>
  )
}