import { AlertTriangle } from 'lucide-react';
import type { Prediction } from '../types/trajectory';

interface FallbackAlertProps {
  predictions: Prediction[] | null;
}

export default function FallbackAlert({ predictions }: FallbackAlertProps) {
  if (!predictions) return null;
  const fallbacks = predictions.filter(p => p.fallback_used);
  if (fallbacks.length === 0) return null;

  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-amber-400" />
        <h3 className="text-sm font-semibold text-amber-300">Degraded Prediction</h3>
      </div>
      <p className="text-xs text-amber-200/80">
        Environmental data is incomplete or invalid for {fallbacks.length} of {predictions.length} horizons.
        The system safely switched to <strong>Persistence fallback</strong>.
      </p>
      <p className="text-xs text-amber-200/60">
        Predicted displacement: <strong>0 m</strong>. Coordinates remain at the latest observed iceberg position.
      </p>
    </div>
  );
}
