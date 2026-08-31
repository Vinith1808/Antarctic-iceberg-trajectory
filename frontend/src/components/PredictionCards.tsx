import type { Prediction } from '../types/trajectory';
import { HORIZON_COLORS, HORIZON_LABELS } from '../types/trajectory';
import { displacementKm, formatCoord } from '../utils/coordinates';
import { MapPin, Navigation } from 'lucide-react';

interface PredictionCardsProps {
  predictions: Prediction[];
  activeHorizon: number | null;
  onSelectHorizon: (h: number) => void;
}

export default function PredictionCards({ predictions, activeHorizon, onSelectHorizon }: PredictionCardsProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Forecast Horizons</h3>
      <div className="grid gap-2">
        {predictions.map(p => {
          const h = p.horizon_hours;
          const color = HORIZON_COLORS[h] || '#888';
          const isActive = activeHorizon === h;
          const disp = displacementKm(p.predicted_dx_m, p.predicted_dy_m);
          return (
            <button key={h} onClick={() => onSelectHorizon(h)}
              className={`text-left rounded-lg border p-3 transition-all ${
                isActive
                  ? 'border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/5'
                  : 'border-slate-700/50 bg-slate-800/30 hover:bg-slate-700/30'
              }`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
                  <span className="text-sm font-medium text-white">{HORIZON_LABELS[h]}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  p.fallback_used
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-emerald-500/15 text-emerald-400'
                }`}>
                  {p.prediction_quality}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-400">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {formatCoord(p.predicted_latitude)}°</span>
                <span className="flex items-center gap-1"><Navigation className="w-3 h-3" /> {formatCoord(p.predicted_longitude)}°</span>
                <span>Δ {disp.toFixed(1)} km</span>
                <span className="text-slate-500">{p.selected_model}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
