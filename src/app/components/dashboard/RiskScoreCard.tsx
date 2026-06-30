// src/app/components/dashboard/RiskScoreCard.tsx
interface RiskProps {
  riskScore: number;
  riskColor: string;
}

export default function RiskScoreCard({ riskScore, riskColor }: RiskProps) {
  return (
    <div className="glass-card p-6 flex justify-between items-center" style={{ minHeight: '120px' }}>
      <div>
        <h3 className="stat-label mb-1">AI Risk Score</h3>
        <p className="text-slate-400 text-xs uppercase tracking-wider">
          {riskScore > 70 ? '🚨 Critical Risk Detected' : riskScore > 40 ? '⚠️ Elevated Risk' : '✅ Normal Operations'}
        </p>
      </div>
      <p className={`text-6xl font-black text-${riskColor}-500`}>
        {riskScore}<span className="text-2xl text-slate-500">/100</span>
      </p>
    </div>
  );
}