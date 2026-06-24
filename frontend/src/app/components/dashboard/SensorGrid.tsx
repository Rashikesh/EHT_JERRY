// src/app/components/dashboard/SensorGrid.tsx
interface SensorGridProps {
  gas: number;
  pressure: number;
  temperature: number;
}

export default function SensorGrid({ gas, pressure, temperature }: SensorGridProps) {
  return (
    <div className="sensor-grid">
      <div className={`glass-card p-6 stat-box ${gas > 40 ? 'border-red-500/50' : ''}`}>
        <h3 className="stat-label">Gas Level</h3>
        <p className={`stat-value ${gas > 40 ? 'danger' : ''}`}>{gas}%</p>
        {gas > 40 && <p className="text-red-400 font-bold mt-2 text-sm">⚠️ CRITICAL DANGER</p>}
      </div>
      <div className="glass-card p-6 stat-box">
        <h3 className="stat-label">Pressure</h3>
        <p className="stat-value">{pressure} <span className="text-lg text-slate-400">bar</span></p>
      </div>
      <div className="glass-card p-6 stat-box">
        <h3 className="stat-label">Temperature</h3>
        <p className="stat-value">{temperature}°C</p>
      </div>
    </div>
  );
}