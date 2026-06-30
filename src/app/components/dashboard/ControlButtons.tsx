// src/app/components/dashboard/ControlButtons.tsx
export default function ControlButtons() {
  const handleEmergency = () => fetch('http://localhost:8000/force-emergency', { method: 'POST' });
  const handleReset = () => fetch('http://localhost:8000/reset-sensors', { method: 'POST' });

  return (
    <div className="flex justify-center gap-4">
      <button onClick={handleEmergency} className="action-btn emergency">
        🚨 SIMULATE EMERGENCY
      </button>
      <button onClick={handleReset} className="action-btn reset">
        🔄 Reset to Normal
      </button>
    </div>
  );
}