import type { ModelInfoResponse } from '../types/trajectory';
import { Cpu, ArrowRight } from 'lucide-react';

interface ModelStatusProps {
  modelInfo: ModelInfoResponse | null;
  velocity: number;
  selectedModel: string | null;
}

export default function ModelStatus({ modelInfo, velocity, selectedModel }: ModelStatusProps) {
  if (!modelInfo) return null;
  const threshold = modelInfo.threshold_ms;
  const regime = velocity < threshold ? 'STATIONARY / SLOW' : 'MOVING';
  const routedModel = velocity < threshold ? 'Persistence' : 'Physics B';

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-4 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Cpu className="w-4 h-4 text-cyan-400" />
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prediction Engine</h3>
      </div>
      <p className="text-sm font-medium text-white">Regime-Aware Hybrid</p>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between text-slate-400">
          <span>Current Regime</span>
          <span className={`font-medium ${velocity >= threshold ? 'text-orange-400' : 'text-cyan-400'}`}>{regime}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Routed Model</span>
          <span className="text-white font-medium">{selectedModel || routedModel}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Velocity</span>
          <span className="text-white font-mono">{velocity.toFixed(4)} m/s</span>
        </div>
      </div>

      <div className="border-t border-slate-700/50 pt-2 text-xs text-slate-500">
        <p className="flex items-center gap-1">v &lt; {threshold} m/s <ArrowRight className="w-3 h-3" /> Persistence</p>
        <p className="flex items-center gap-1">v ≥ {threshold} m/s <ArrowRight className="w-3 h-3" /> Physics B</p>
      </div>
    </div>
  );
}
