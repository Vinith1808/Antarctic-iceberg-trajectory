import { Info } from 'lucide-react';

export default function Limitations() {
  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-4 space-y-2">
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 text-slate-400" />
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Model Limitations</h3>
      </div>
      <ul className="text-xs text-slate-500 space-y-1 list-disc list-inside">
        <li>Long-horizon predictions (&gt;240h) accumulate significant uncertainty.</li>
        <li>High-velocity icebergs (e.g. d27) can produce large endpoint errors.</li>
        <li>Storm events, grounding, and collisions are not explicitly modeled.</li>
        <li>Initial velocity quality strongly affects prediction accuracy.</li>
        <li>The system uses a regime-aware physical/persistence policy — not a statistical confidence model.</li>
      </ul>
    </div>
  );
}
