// src/app/components/dashboard/PermitStatusPanel.tsx
interface PermitProps {
  permitActive: boolean;
  aiJustification: string;
  confidence?: number;
  gas: number;
  pressure: number;
  temperature: number;
}

export default function PermitStatusPanel({ permitActive, aiJustification, confidence, gas, pressure, temperature }: PermitProps) {
  
  //  AI OBSERVABILITY ENGINE: Correlates sensors to find Root Cause
  const getRootCause = () => {
    if (gas > 40 && temperature > 60) return { type: 'Thermal Runaway Leak', icon: '🔥' };
    if (gas > 40 && pressure > 2500) return { type: 'High-Pressure Valve Failure', icon: '' };
    if (gas > 40) return { type: 'Standard Gas Accumulation', icon: '💨' };
    if (pressure > 2600) return { type: 'Over-Pressurization', icon: '️' };
    return { type: 'System Anomaly', icon: '❓' };
  };

  // ️ Dynamic Troubleshooting Checklist based on Root Cause
  const getTroubleshootingSteps = () => {
    const cause = getRootCause().type;
    if (cause.includes('Thermal')) return ['1. Activate emergency cooling systems.', '2. Evacuate Zone B immediately.', '3. Inspect heat exchangers for blockages.'];
    if (cause.includes('Pressure')) return ['1. Close main isolation valves.', '2. Vent pressure via manual release.', '3. Check SCADA for pump malfunctions.'];
    return ['1. Verify sensor calibration.', '2. Check for physical leaks in Zone B.', '3. Reset PLC interlock after clearance.'];
  };

  const rootCause = getRootCause();
  const steps = getTroubleshootingSteps();

  return (
    <div className={`h-auto min-h-[400px] max-h-[550px] p-6 rounded-2xl border transition-all duration-500 flex flex-col overflow-y-auto mb-6 ${
      !permitActive 
        ? 'bg-red-500/10 border-red-500/40 shadow-[0_0_30px_rgba(239,68,68,0.2)]' 
        : 'bg-green-500/5 border-green-500/20'
    }`}>
      
      <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Digital Permit Intelligence</h2>
      
      <p className={`text-3xl font-black mb-3 ${!permitActive ? 'text-red-400' : 'text-green-400'}`}>
        {permitActive ? '🟢 PERMIT ACTIVE' : '🔴 PERMIT BLOCKED'}
      </p>
      
      <p className="text-slate-400 text-sm mb-6">
        {permitActive 
          ? 'Environmental parameters are within safe limits. Work may proceed.' 
          : 'PLC Interlock Triggered. All hot work is immediately suspended.'}
      </p>
      
      {/* Compact Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-black/30 p-3 rounded-lg border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase font-bold">AI Confidence</p>
          <p className="text-xl font-bold text-yellow-400">{confidence || 0}%</p>
        </div>
        <div className="bg-black/30 p-3 rounded-lg border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase font-bold">Latency</p>
          <p className="text-xl font-bold text-blue-400">&lt;50ms</p>
        </div>
      </div>

      {/* 🆕 NEW: AI Troubleshooting Console (Only shows when Blocked) */}
      {!permitActive && (
        <div className="mt-auto space-y-4 animate-fade-in">
          {/* Root Cause Analyzer */}
          <div className="bg-red-950/40 border border-red-500/30 rounded-lg p-4">
            <h3 className="text-red-400 font-bold text-xs uppercase mb-2 flex items-center gap-2">
              🧠 AI Root Cause Analysis
            </h3>
            <p className="text-white text-lg font-bold flex items-center gap-2">
              {rootCause.icon} {rootCause.type}
            </p>
            <p className="text-slate-400 text-xs mt-1">
              Correlated Gas ({gas}%), Pressure ({pressure} bar), Temp ({temperature}°C)
            </p>
          </div>

          {/* Actionable Maintenance Checklist */}
          <div className="bg-black/40 border border-yellow-500/20 rounded-lg p-4">
            <h3 className="text-yellow-400 font-bold text-xs uppercase mb-3 flex items-center gap-2">
              🛠️ Recommended Troubleshooting Steps
            </h3>
            <ul className="space-y-2">
              {steps.map((step, index) => (
                <li key={index} className="flex items-start gap-3 text-sm text-slate-300">
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

      {/* AI Justification Box (Shows when Active or as fallback) */}
      {permitActive && aiJustification && (
        <div className="mt-auto bg-black/40 border border-green-500/20 rounded-lg p-3">
          <h3 className="text-green-400 font-bold text-[10px] uppercase mb-1">🧠 AI Safety Justification</h3>
          <p className="text-slate-300 text-xs whitespace-pre-wrap leading-relaxed">{aiJustification}</p>
        </div>
      )}
    </div>
  );
}