"use client"

import {
  MapContainer,
  TileLayer,
  Circle,
  CircleMarker,
  Popup,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"

interface IoTAsset {
  id: string
  name: string
  lat: number
  lng: number
  status: "learning" | "active" | "critical"
  gasLevel: number
  learnedThreshold: number
}

interface PlantMapProps {
  assets: IoTAsset[]
  isDanger: boolean
}

export default function PlantMap({ assets, isDanger }: PlantMapProps) {
  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={[28.6139, 77.209]}
        zoom={16}
        className="w-full h-full rounded-xl z-0"
        zoomControl={false}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {assets.map((asset) => {
          let radius = 50
          let color = "#22c55e"
          let pulseClass = ""

          if (asset.status === "learning") {
            radius = 30
            color = "#3b82f6"
            pulseClass = "animate-pulse"
          } else if (asset.status === "critical") {
            const excess = asset.gasLevel - asset.learnedThreshold
            radius = 50 + excess * 10
            color = "#ef4444"
            pulseClass = "animate-ping"
          }

          return (
            <div key={asset.id}>
              <Circle
                center={[asset.lat, asset.lng]}
                radius={radius}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: asset.status === "critical" ? 0.4 : 0.1,
                  weight: 2,
                }}
                className={pulseClass}
              />

              <CircleMarker
                center={[asset.lat, asset.lng]}
                radius={8}
                pathOptions={{
                  color: "#fff",
                  fillColor: color,
                  fillOpacity: 1,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="text-slate-900 p-2 min-w-[150px]">
                    <h3 className="font-bold text-sm mb-1">{asset.name}</h3>
                    <p className="text-xs">
                      Status:{" "}
                      <span className="font-bold uppercase" style={{ color }}>
                        {asset.status}
                      </span>
                    </p>
                    {asset.status !== "learning" && (
                      <>
                        <p className="text-xs mt-1">Gas: {asset.gasLevel}%</p>
                        <p className="text-xs text-slate-500">
                          AI Baseline: {asset.learnedThreshold}%
                        </p>
                      </>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            </div>
          )
        })}
      </MapContainer>
    </div>
  )
}
