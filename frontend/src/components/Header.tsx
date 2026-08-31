import { Snowflake, Wifi, WifiOff, Loader } from 'lucide-react';
import type { ConnectionStatus } from '../types/trajectory';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  modelReady: boolean;
  lastPredictionTime: string | null;
}

export default function Header({ connectionStatus, modelReady, lastPredictionTime }: HeaderProps) {
  return (
    <header className="bg-slate-900 border-b border-slate-700/50 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Snowflake className="w-7 h-7 text-cyan-400" />
        <div>
          <h1 className="text-lg font-semibold text-white tracking-tight">
            Antarctic Iceberg Trajectory Intelligence
          </h1>
          <p className="text-xs text-slate-400">
            Regime-Aware Hybrid Prediction Engine
          </p>
        </div>
      </div>
      <div className="flex items-center gap-5 text-sm">
        <StatusPill
          label="API"
          status={connectionStatus === 'connected' ? 'ok' : connectionStatus === 'checking' ? 'loading' : 'error'}
        />
        <StatusPill
          label="Model"
          status={modelReady ? 'ok' : 'error'}
        />
        {lastPredictionTime && (
          <span className="text-slate-400 text-xs">
            Last: {new Date(lastPredictionTime).toLocaleTimeString()}
          </span>
        )}
      </div>
    </header>
  );
}

function StatusPill({ label, status }: { label: string; status: 'ok' | 'error' | 'loading' }) {
  const icon =
    status === 'ok' ? <Wifi className="w-3.5 h-3.5" /> :
    status === 'loading' ? <Loader className="w-3.5 h-3.5 animate-spin" /> :
    <WifiOff className="w-3.5 h-3.5" />;

  const color =
    status === 'ok' ? 'text-emerald-400' :
    status === 'loading' ? 'text-amber-400' :
    'text-red-400';

  return (
    <span className={`flex items-center gap-1.5 ${color}`}>
      {icon}
      <span className="text-slate-300">{label}</span>
    </span>
  );
}
