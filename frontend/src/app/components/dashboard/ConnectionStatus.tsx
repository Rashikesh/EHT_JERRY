// src/app/components/dashboard/ConnectionStatus.tsx
export default function ConnectionStatus({ status }: { status: string }) {
  const isConnected = status === 'Connected to PLC';

  return (
    <div className={`connection-status w-full px-6 py-3 rounded-lg border-2 flex items-center justify-between ${
      isConnected 
        ? 'connected bg-green-500/10 border-green-500/50' 
        : 'disconnected bg-red-500/10 border-red-500/50'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
        <span className={`font-bold text-sm uppercase tracking-wider ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
          Backend Connection: {isConnected ? 'CONNECTED' : status.toUpperCase()}
        </span>
      </div>
      <div className={`text-xs ${isConnected ? 'text-green-300' : 'text-red-300'}`}>
        {isConnected ? '✓ Receiving live telemetry' : '⚠ Waiting for data stream...'}
      </div>
    </div>
  );
}