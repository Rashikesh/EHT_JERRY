"use client"
import { useEffect, useState } from "react"

interface TimelineEvent {
  time: string
  event: string
  detail: string
  type: string // "PERMIT", "SHIFT", "BLOCK"
}

export default function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="bg-slate-900 border border-slate-700 margin:10px rounded-lg p-4 h-full">
      <h3 className="text-white font-bold mb-4 flex items-center gap-2">
        📍 Incident Timeline (Visakhapatnam Scenario)
      </h3>
      <div className="space-y-4 relative">
        {/* Vertical line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>

        {events.map((evt, idx) => (
          <div key={idx} className="relative pl-10">
            {/* Dot on the line */}
            <div
              className={`absolute left-3 top-1.5 w-3 h-3 rounded-full border-2 border-slate-900 ${
                evt.type === "BLOCK"
                  ? "bg-red-500"
                  : evt.type === "PERMIT"
                    ? "bg-blue-500"
                    : "bg-yellow-500"
              }`}
            ></div>

            <div
              className={`p-3 rounded-lg border ${
                evt.type === "BLOCK"
                  ? "bg-red-900/30 border-red-500/50"
                  : "bg-slate-800 border-slate-700"
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span
                  className={`font-bold text-sm ${
                    evt.type === "BLOCK" ? "text-red-400" : "text-white"
                  }`}
                >
                  {evt.event}
                </span>
                <span className="text-slate-500 text-xs font-mono">
                  {evt.time}
                </span>
              </div>
              <p className="text-slate-400 text-xs">{evt.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
