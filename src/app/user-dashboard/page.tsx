"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import {api} from "@/lib/api"

interface DashboardSummary {
  total_sites: number
  open_points: number
  closed_points: number
  recent_errors: number
  active_users: number
}

interface Activity {
  id: number
  user_id: number
  site_id: number | null
  action: string
  timestamp: string
  metadata: any
  username: string
}

interface Point {
  id: number
  site_id: number
  title: string
  status: string
  severity: string
  description: string | null
  created_at: string
  closed_at: string | null
  closed_by: number | null
  site_name: string
}

interface Error {
  id: number
  site_id: number
  error_type: string
  message: string
  timestamp: string
  resolved: boolean
  resolved_at: string | null
  site_name: string
}

interface Site {
  id: number
  name: string
  location: string | null
  latitude: number | null
  longitude: number | null
  status: string
  created_at: string
  owner_id: number
}

export default function UserDashboard() {
  const { user, isAuthenticated, logout, isLoading } = useAuth()
  const router = useRouter()

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [openPoints, setOpenPoints] = useState<Point[]>([])
  const [closedPoints, setClosedPoints] = useState<Point[]>([])
  const [errors, setErrors] = useState<Error[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [activeTab, setActiveTab] = useState("overview")

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login")
      return
    }

    if (isAuthenticated) {
      fetchData()
    }
  }, [isAuthenticated, isLoading])

  const fetchData = async () => {
    try {
      const [
        summaryRes,
        activitiesRes,
        openRes,
        closedRes,
        errorsRes,
        sitesRes,
      ] = await Promise.all([
        api.get("/dashboard/summary"),
        api.get("/dashboard/activity?limit=20"),
        api.get("/dashboard/points?status=open&limit=20"),
        api.get("/dashboard/points?status=closed&limit=20"),
        api.get("/dashboard/errors?limit=20"),
        api.get("/dashboard/sites"),
      ])

      setSummary(summaryRes.data)
      setActivities(activitiesRes.data)
      setOpenPoints(openRes.data)
      setClosedPoints(closedRes.data)
      setErrors(errorsRes.data)
      setSites(sitesRes.data)
    } catch (error) {
      console.error("Failed to fetch data:", error)
    }
  }

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <div className="bg-slate-800/50 backdrop-blur-xl border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">👤 User Dashboard</h1>
            <p className="text-slate-400 text-sm">
              Welcome back, {user?.full_name}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
            >
              Safety Dashboard
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded-lg text-sm font-medium transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-2 mb-6 border-b border-slate-700 overflow-x-auto">
          {["overview", "activity", "sites", "points", "errors"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition whitespace-nowrap ${
                activeTab === tab
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="space-y-6">
          {activeTab === "overview" && summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Sites"
                value={summary.total_sites}
                icon="🏭"
                color="blue"
              />
              <StatCard
                title="Open Points"
                value={summary.open_points}
                icon="🟢"
                color="green"
              />
              <StatCard
                title="Closed Points"
                value={summary.closed_points}
                icon="🔴"
                color="red"
              />
              <StatCard
                title="Recent Errors"
                value={summary.recent_errors}
                icon="⚠️"
                color="yellow"
              />
            </div>
          )}

          {activeTab === "activity" && (
            <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                📝 Activity Log
              </h2>
              <div className="space-y-3">
                {activities.map((activity) => (
                  <div
                    key={activity.id}
                    className="bg-slate-900/50 border border-slate-700 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-blue-400 font-bold text-sm">
                        {activity.action}
                      </span>
                      <span className="text-slate-500 text-xs">
                        {new Date(activity.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-slate-400 text-xs">
                      by {activity.username}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "sites" && (
            <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl p-6">
              <h2 className="text-xl font-bold text-white mb-4">🏭 Sites</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sites.map((site) => (
                  <div
                    key={site.id}
                    className="bg-slate-900/50 border border-slate-700 rounded-lg p-4"
                  >
                    <h3 className="text-white font-bold mb-2">{site.name}</h3>
                    <p className="text-slate-400 text-sm mb-2">
                      {site.location || "No location"}
                    </p>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        site.status === "active"
                          ? "bg-green-500/20 text-green-400"
                          : site.status === "maintenance"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {site.status.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "points" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">
                  🟢 Open Points
                </h2>
                <div className="space-y-3">
                  {openPoints.map((point) => (
                    <PointCard key={point.id} point={point} />
                  ))}
                </div>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">
                  🔴 Closed Points
                </h2>
                <div className="space-y-3">
                  {closedPoints.map((point) => (
                    <PointCard key={point.id} point={point} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "errors" && (
            <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                ⚠️ Error History
              </h2>
              <div className="space-y-3">
                {errors.map((error) => (
                  <div
                    key={error.id}
                    className="bg-red-900/20 border border-red-500/30 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-red-400 font-bold text-sm">
                        {error.error_type}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          error.resolved
                            ? "bg-green-500/20 text-green-400"
                            : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {error.resolved ? "RESOLVED" : "UNRESOLVED"}
                      </span>
                    </div>
                    <p className="text-slate-300 text-sm mb-2">
                      {error.message}
                    </p>
                    <p className="text-slate-500 text-xs">
                      Site: {error.site_name}
                    </p>
                    <p className="text-slate-500 text-xs">
                      {new Date(error.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string
  value: number
  icon: string
  color: string
}) {
  const colorClasses = {
    blue: "bg-blue-600/20 border-blue-500/30 text-blue-400",
    green: "bg-green-600/20 border-green-500/30 text-green-400",
    red: "bg-red-600/20 border-red-500/30 text-red-400",
    yellow: "bg-yellow-600/20 border-yellow-500/30 text-yellow-400",
  }

  return (
    <div
      className={`${colorClasses[color as keyof typeof colorClasses]} border rounded-xl p-6`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <span className="text-3xl font-bold">{value}</span>
      </div>
      <p className="text-sm font-medium">{title}</p>
    </div>
  )
}

function PointCard({ point }: { point: Point }) {
  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-white font-bold text-sm">{point.title}</h3>
        <span
          className={`text-xs px-2 py-1 rounded ${
            point.severity === "critical"
              ? "bg-red-500/20 text-red-400"
              : point.severity === "high"
                ? "bg-orange-500/20 text-orange-400"
                : point.severity === "medium"
                  ? "bg-yellow-500/20 text-yellow-400"
                  : "bg-green-500/20 text-green-400"
          }`}
        >
          {point.severity.toUpperCase()}
        </span>
      </div>
      <p className="text-slate-400 text-xs mb-2">Site: {point.site_name}</p>
      {point.description && (
        <p className="text-slate-300 text-sm">{point.description}</p>
      )}
      <p className="text-slate-500 text-xs mt-2">
        {new Date(point.created_at).toLocaleString()}
      </p>
    </div>
  )
}
