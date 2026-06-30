// src/app/components/dashboard/PermitStatusPanel.tsx
interface SimilarIncident {
  id: string
  date: string
  cause: string
  outcome: string
  lessons: string
  similarity_score: number
}

interface PermitProps {
  permitActive: boolean
  aiJustification: string
  confidence?: number
  gas: number
  pressure: number
  temperature: number
  anomalyScore?: number
  isCompoundRisk?: boolean
  similarIncidents?: SimilarIncident[]
}

export default function PermitStatusPanel({
  permitActive,
  aiJustification,
  confidence,
  gas,
  pressure,
  temperature,
  anomalyScore = 0,
  isCompoundRisk = false,
  similarIncidents = [],
}: PermitProps) {
  const isCompound =
    isCompoundRisk || aiJustification?.includes("COMPOUND RISK")

  const getRootCause = () => {
    if (gas > 40 && temperature > 60)
      return { type: "Thermal Runaway Leak", icon: "🔥" }
    if (gas > 40 && pressure > 2500)
      return { type: "High-Pressure Valve Failure", icon: "⚠️" }
    if (gas > 40) return { type: "Standard Gas Accumulation", icon: "💨" }
    if (pressure > 2600) return { type: "Over-Pressurization", icon: "🔴" }
    return { type: "System Anomaly", icon: "❓" }
  }

  const getTroubleshootingSteps = () => {
    const cause = getRootCause().type
    if (cause.includes("Thermal"))
      return [
        "1. Activate emergency cooling systems.",
        "2. Evacuate Zone B immediately.",
        "3. Inspect heat exchangers for blockages.",
      ]
    if (cause.includes("Pressure"))
      return [
        "1. Close main isolation valves.",
        "2. Vent pressure via manual release.",
        "3. Check SCADA for pump malfunctions.",
      ]
    return [
      "1. Verify sensor calibration.",
      "2. Check for physical leaks in Zone B.",
      "3. Reset PLC interlock after clearance.",
    ]
  }

  const rootCause = getRootCause()
  const steps = getTroubleshootingSteps()

  const getContainerStyle = () => {
    if (permitActive)
      return "bg-gradient-to-br from-green-900/20 via-emerald-950/30 to-green-900/20 border-green-500/40 shadow-[0_0_60px_rgba(34,197,94,0.3)]"
    if (isCompound)
      return "bg-gradient-to-br from-orange-900/20 via-amber-950/30 to-orange-900/20 border-orange-500/40 shadow-[0_0_60px_rgba(249,115,22,0.3)]"
    return "bg-gradient-to-br from-red-900/20 via-rose-950/30 to-red-900/20 border-red-500/40 shadow-[0_0_60px_rgba(239,68,68,0.3)]"
  }

  const getStatusColor = () => {
    if (permitActive) return "text-green-400"
    if (isCompound) return "text-orange-400"
    return "text-red-400"
  }

  const getStatusText = () => {
    if (permitActive) return "🟢 PERMIT ACTIVE"
    if (isCompound) return "🧠 COMPOUND RISK DETECTED"
    return "🔴 PERMIT BLOCKED"
  }

  const getStatusMessage = () => {
    if (permitActive)
      return "Environmental parameters are within safe limits. Work may proceed."
    if (isCompound)
      return "AI detected dangerous combination of conditions. PLC Interlock triggered."
    return "PLC Interlock Triggered. All hot work is immediately suspended."
  }

  const getMlRiskColor = () => {
    if (anomalyScore < -0.2) return "text-red-400"
    if (anomalyScore < 0) return "text-yellow-400"
    return "text-green-400"
  }

  return (
    <div
      className={`h-auto min-h-[400px] max-h-[700px] p-6 rounded-2xl border transition-all duration-500 flex flex-col overflow-y-auto mb-6 ${getContainerStyle()}`}
    >
      <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">
        Digital Permit Intelligence
      </h2>

      <p className={`text-3xl font-black mb-3 ${getStatusColor()}`}>
        {getStatusText()}
      </p>

      <p className="text-slate-400 text-sm mb-6">{getStatusMessage()}</p>

      {isCompound && !permitActive && (
        <div className="bg-orange-900/30 border border-orange-500/40 rounded-lg p-3 mb-4">
          <p className="text-orange-400 text-xs font-bold uppercase mb-1">
            ⚠️ Multi-Factor Risk Analysis
          </p>
          <p className="text-slate-300 text-xs">
            This is not a simple threshold breach. The AI detected a dangerous
            combination of conditions that no single sensor would flag alone.
          </p>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-black/30 p-3 rounded-lg border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase font-bold">
            AI Confidence
          </p>
          <p
            className={`text-xl font-bold ${isCompound ? "text-orange-400" : "text-yellow-400"}`}
          >
            {confidence || 0}%
          </p>
        </div>

        <div className="bg-black/30 p-3 rounded-lg border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase font-bold">
            ML Anomaly
          </p>
          <p className={`text-xl font-bold ${getMlRiskColor()}`}>
            {anomalyScore.toFixed(2)}
          </p>
        </div>

        <div className="bg-black/30 p-3 rounded-lg border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase font-bold">
            Latency
          </p>
          <p className="text-xl font-bold text-blue-400">&lt;50ms</p>
        </div>
      </div>

      {!permitActive && (
        <div className="mt-auto space-y-4 animate-fade-in">
          {/* Root Cause Analyzer */}
          <div
            className={`border rounded-lg p-4 ${
              isCompound
                ? "bg-orange-950/40 border-orange-500/30"
                : "bg-red-950/40 border-red-500/30"
            }`}
          >
            <h3
              className={`font-bold text-xs uppercase mb-2 flex items-center gap-2 ${
                isCompound ? "text-orange-400" : "text-red-400"
              }`}
            >
              🧠 AI Root Cause Analysis
            </h3>
            <p className="text-white text-lg font-bold flex items-center gap-2">
              {rootCause.icon} {rootCause.type}
            </p>
            <p className="text-slate-400 text-xs mt-1">
              Correlated Gas ({gas}%), Pressure ({pressure} bar), Temp (
              {temperature}°C)
            </p>
          </div>

          {/* 🆕 NEW: Similar Historical Incidents */}
          {similarIncidents && similarIncidents.length > 0 && (
            <div className="bg-purple-950/40 border border-purple-500/30 rounded-lg p-4">
              <h3 className="text-purple-400 font-bold text-xs uppercase mb-3 flex items-center gap-2">
                📚 Similar Historical Incidents
              </h3>
              <div className="space-y-3">
                {similarIncidents.slice(0, 2).map((incident, idx) => (
                  <div
                    key={idx}
                    className="bg-black/30 rounded-lg p-3 border border-purple-500/20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-bold text-sm">
                        {incident.id}
                      </span>
                      <span className="text-purple-400 text-xs font-bold">
                        {incident.similarity_score}% similar
                      </span>
                    </div>
                    <p className="text-slate-300 text-xs mb-1">
                      <span className="text-slate-500">Date:</span>{" "}
                      {incident.date}
                    </p>
                    <p className="text-slate-300 text-xs mb-1">
                      <span className="text-slate-500">Cause:</span>{" "}
                      {incident.cause}
                    </p>
                    <p className="text-slate-300 text-xs mb-1">
                      <span className="text-slate-500">Outcome:</span>{" "}
                      {incident.outcome}
                    </p>
                    <p className="text-yellow-400 text-xs mt-2 italic">
                      💡 Lesson: {incident.lessons}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Troubleshooting Steps */}
          <div className="bg-black/40 border border-yellow-500/20 rounded-lg p-4">
            <h3 className="text-yellow-400 font-bold text-xs uppercase mb-3 flex items-center gap-2">
              🛠️ Recommended Troubleshooting Steps
            </h3>
            <ul className="space-y-2">
              {steps.map((step, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-sm text-slate-300"
                >
                  <span className="bg-yellow-500/20 text-yellow-400 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {aiJustification && (
        <div
          className={`mt-auto border rounded-lg p-3 ${
            isCompound && !permitActive
              ? "bg-orange-900/20 border-orange-500/30"
              : permitActive
                ? "bg-black/40 border-green-500/20"
                : "bg-black/40 border-red-500/20"
          }`}
        >
          <h3
            className={`font-bold text-[10px] uppercase mb-1 ${
              isCompound && !permitActive
                ? "text-orange-400"
                : permitActive
                  ? "text-green-400"
                  : "text-red-400"
            }`}
          >
            🧠 AI Safety Justification
          </h3>
          <p className="text-slate-300 text-xs whitespace-pre-wrap leading-relaxed">
            {aiJustification}
          </p>
        </div>
      )}
    </div>
  )
}
