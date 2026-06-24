// src/app/components/PlantMap.tsx
'use client'

import { MapContainer, TileLayer, Circle, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface IoTAsset {
  id: string;
  name: string;
  lat: number;
  lng: number;
  status: 'learning' | 'active' | 'critical';
  gasLevel: number;
  learnedThreshold: number;
}

interface PlantMapProps {
  assets: IoTAsset[];
  isDanger: boolean;
}

export default function PlantMap({ assets, isDanger }: PlantMapProps) {
  return (
    <MapContainer 
      center={[28.6139, 77.2090]} 
      zoom={16} 
      style={{ height: '100%', width: '100%', borderRadius: '12px' }}
      zoomControl={false}
    >
      {/* Dark Mode Map Tiles */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {assets.map((asset) => {
        // 🧠 Self-Harnessing Logic: Calculate dynamic radius based on status
        let radius = 50; // Default safe radius in meters
        let color = '#22c55e'; // Green
        let pulseClass = '';

        if (asset.status === 'learning') {
          radius = 30;
          color = '#3b82f6'; // Blue for learning
          pulseClass = 'animate-pulse';
        } else if (asset.status === 'critical') {
          // Dynamic Geofencing: Radius expands based on how far gas exceeds threshold
          const excess = asset.gasLevel - asset.learnedThreshold;
          radius = 50 + (excess * 10); // Expands by 10 meters per 1% excess gas
          color = '#ef4444'; // Red
          pulseClass = 'animate-ping';
        }

        return (
          <div key={asset.id}>
            {/* The Dynamic Danger Geofence */}
            <Circle
              center={[asset.lat, asset.lng]}
              radius={radius}
              pathOptions={{ 
                color: color, 
                fillColor: color, 
                fillOpacity: asset.status === 'critical' ? 0.4 : 0.1,
                weight: 2
              }}
              className={pulseClass}
            />
            
            {/* The Sensor Node */}
            <CircleMarker 
              center={[asset.lat, asset.lng]} 
              radius={8} 
              pathOptions={{ color: '#fff', fillColor: color, fillOpacity: 1, weight: 2 }}
            >
              <Popup>
                <div className="text-slate-900 p-2">
                  <h3 className="font-bold text-sm">{asset.name}</h3>
                  <p className="text-xs">Status: <span className="font-bold uppercase" style={{color}}>{asset.status}</span></p>
                  {asset.status !== 'learning' && (
                    <>
                      <p className="text-xs">Gas: {asset.gasLevel}%</p>
                      <p className="text-xs text-slate-500">AI Baseline: {asset.learnedThreshold}%</p>
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          </div>
        );
      })}
    </MapContainer>
  )
}