import { Wind, Waves, Snowflake } from 'lucide-react';

interface EnvironmentPanelProps {
  uo: number | null | undefined;
  vo: number | null | undefined;
  u10: number | null | undefined;
  v10: number | null | undefined;
  siconc: number | null | undefined;
  velocity: number;
  heading: number;
}

export default function EnvironmentPanel({ uo, vo, u10, v10, siconc, velocity, heading }: EnvironmentPanelProps) {
  const oceanSpeed = uo != null && vo != null ? Math.sqrt(uo * uo + vo * vo) : null;
  const windSpeed = u10 != null && v10 != null ? Math.sqrt(u10 * u10 + v10 * v10) : null;

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-4 space-y-3">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Environmental State</h3>

      <EnvGroup icon={<Waves className="w-4 h-4 text-blue-400" />} label="Ocean Current" available={uo != null && vo != null}>
        {uo != null && vo != null ? (
          <div className="grid grid-cols-3 gap-2 text-xs text-slate-300">
            <span>U: {uo.toFixed(3)}</span>
            <span>V: {vo.toFixed(3)}</span>
            <span>{oceanSpeed!.toFixed(3)} m/s</span>
          </div>
        ) : <span className="text-xs text-slate-500">Not provided</span>}
      </EnvGroup>

      <EnvGroup icon={<Wind className="w-4 h-4 text-teal-400" />} label="Wind (10m)" available={u10 != null && v10 != null}>
        {u10 != null && v10 != null ? (
          <div className="grid grid-cols-3 gap-2 text-xs text-slate-300">
            <span>U: {u10.toFixed(1)}</span>
            <span>V: {v10.toFixed(1)}</span>
            <span>{windSpeed!.toFixed(1)} m/s</span>
          </div>
        ) : <span className="text-xs text-slate-500">Not provided</span>}
      </EnvGroup>

      <EnvGroup icon={<Snowflake className="w-4 h-4 text-sky-300" />} label="Sea Ice" available={siconc != null}>
        {siconc != null ? (
          <div className="text-xs text-slate-300">
            SIC: {(siconc * 100).toFixed(1)}%
          </div>
        ) : <span className="text-xs text-slate-500">Not provided</span>}
      </EnvGroup>

      <div className="border-t border-slate-700/50 pt-2 space-y-1">
        <p className="text-xs text-slate-400">Iceberg Motion</p>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
          <span>Velocity: {velocity.toFixed(4)} m/s</span>
          <span>Heading: {heading.toFixed(1)}°</span>
        </div>
      </div>
    </div>
  );
}

function EnvGroup({ icon, label, available, children }: { icon: React.ReactNode; label: string; available: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">{icon}<span className="text-xs text-slate-300">{label}</span></div>
        <span className={`w-2 h-2 rounded-full ${available ? 'bg-emerald-400' : 'bg-amber-400'}`} />
      </div>
      {children}
    </div>
  );
}
