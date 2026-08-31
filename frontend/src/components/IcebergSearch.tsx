import { useState } from 'react';
import { Send, RotateCcw, Beaker } from 'lucide-react';
import type { TrajectoryRequest, EnvironmentAvailability, PredictionState } from '../types/trajectory';

interface IcebergSearchProps {
  onSubmit: (request: TrajectoryRequest) => void;
  onReset: () => void;
  predictionState: PredictionState;
  apiConnected: boolean;
}

const DEMO_REQUEST: TrajectoryRequest = {
  iceberg_id: 'd27',
  timestamp: '2023-06-15T12:00:00Z',
  latitude: -66.5,
  longitude: -60.2,
  velocity_ms: 0.084,
  heading_deg: 225.0,
  uo: 0.03,
  vo: -0.02,
  u10: 4.5,
  v10: -3.1,
  siconc: 0.15,
};

export default function IcebergSearch({ onSubmit, onReset, predictionState, apiConnected }: IcebergSearchProps) {
  const [form, setForm] = useState<TrajectoryRequest>({
    iceberg_id: '',
    timestamp: new Date().toISOString().slice(0, 16),
    latitude: -65.0,
    longitude: 45.0,
    velocity_ms: 0.05,
    heading_deg: 180.0,
    uo: null,
    vo: null,
    u10: null,
    v10: null,
    siconc: null,
  });
  const [demoMode, setDemoMode] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const envAvailability: EnvironmentAvailability = {
    ocean: form.uo != null && form.vo != null,
    wind: form.u10 != null && form.v10 != null,
    seaIce: form.siconc != null,
  };

  function validate(): boolean {
    const e: Record<string, string> = {};
    if (!form.iceberg_id.trim()) e.iceberg_id = 'Required';
    if (form.latitude < -90 || form.latitude > 90) e.latitude = 'Must be -90 to 90';
    if (form.longitude < -180 || form.longitude > 180) e.longitude = 'Must be -180 to 180';
    if (form.velocity_ms < 0) e.velocity_ms = 'Must be ≥ 0';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    const req: TrajectoryRequest = {
      ...form,
      timestamp: new Date(form.timestamp).toISOString(),
    };
    onSubmit(req);
  }

  function loadDemo() {
    setForm(DEMO_REQUEST);
    setDemoMode(true);
  }

  function handleReset() {
    setDemoMode(false);
    setErrors({});
    onReset();
  }

  function updateField(key: string, value: string) {
    const numericKeys = ['latitude', 'longitude', 'velocity_ms', 'heading_deg', 'uo', 'vo', 'u10', 'v10', 'siconc'];
    if (numericKeys.includes(key)) {
      if (value === '' || value === '-') {
        setForm(f => ({ ...f, [key]: key === 'uo' || key === 'vo' || key === 'u10' || key === 'v10' || key === 'siconc' ? null : 0 }));
      } else {
        setForm(f => ({ ...f, [key]: parseFloat(value) }));
      }
    } else {
      setForm(f => ({ ...f, [key]: value }));
    }
  }

  const isLoading = predictionState === 'loading';

  return (
    <form onSubmit={handleSubmit} className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-5 space-y-4">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Observation Input</h2>
        <button type="button" onClick={loadDemo} className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
          <Beaker className="w-3.5 h-3.5" /> Demo Data
        </button>
      </div>

      {demoMode && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2 text-xs text-amber-300 flex items-center gap-2">
          <Beaker className="w-4 h-4 flex-shrink-0" />
          <span><strong>DEMO MODE</strong> — Pre-filled sample data for iceberg d27</span>
        </div>
      )}

      {/* Iceberg ID + Timestamp */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Iceberg ID" error={errors.iceberg_id}>
          <input value={form.iceberg_id} onChange={e => updateField('iceberg_id', e.target.value)}
            placeholder="e.g. d27" className="input-field" />
        </Field>
        <Field label="Timestamp">
          <input type="datetime-local" value={typeof form.timestamp === 'string' ? form.timestamp.slice(0, 16) : ''}
            onChange={e => updateField('timestamp', e.target.value)} className="input-field" />
        </Field>
      </div>

      {/* Position */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Latitude (°)" error={errors.latitude}>
          <input type="number" step="any" value={form.latitude ?? ''} onChange={e => updateField('latitude', e.target.value)} className="input-field" />
        </Field>
        <Field label="Longitude (°)" error={errors.longitude}>
          <input type="number" step="any" value={form.longitude ?? ''} onChange={e => updateField('longitude', e.target.value)} className="input-field" />
        </Field>
      </div>

      {/* Velocity + Heading */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Velocity (m/s)" error={errors.velocity_ms}>
          <input type="number" step="any" min="0" value={form.velocity_ms ?? ''} onChange={e => updateField('velocity_ms', e.target.value)} className="input-field" />
        </Field>
        <Field label="Heading (°)">
          <input type="number" step="any" value={form.heading_deg ?? ''} onChange={e => updateField('heading_deg', e.target.value)} className="input-field" />
        </Field>
      </div>

      {/* Environment */}
      <div className="border-t border-slate-700/50 pt-3">
        <p className="text-xs text-slate-400 mb-2">Environmental Inputs <span className="text-slate-500">(optional)</span></p>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Ocean U (m/s)">
            <input type="number" step="any" value={form.uo ?? ''} onChange={e => updateField('uo', e.target.value)} placeholder="—" className="input-field" />
          </Field>
          <Field label="Ocean V (m/s)">
            <input type="number" step="any" value={form.vo ?? ''} onChange={e => updateField('vo', e.target.value)} placeholder="—" className="input-field" />
          </Field>
          <Field label="Wind U10 (m/s)">
            <input type="number" step="any" value={form.u10 ?? ''} onChange={e => updateField('u10', e.target.value)} placeholder="—" className="input-field" />
          </Field>
          <Field label="Wind V10 (m/s)">
            <input type="number" step="any" value={form.v10 ?? ''} onChange={e => updateField('v10', e.target.value)} placeholder="—" className="input-field" />
          </Field>
          <Field label="Sea Ice Conc. (0–1)">
            <input type="number" step="any" min="0" max="1" value={form.siconc ?? ''} onChange={e => updateField('siconc', e.target.value)} placeholder="—" className="input-field" />
          </Field>
        </div>
      </div>

      {/* Environment Availability */}
      <div className="flex gap-4 text-xs">
        <EnvBadge label="Ocean" available={envAvailability.ocean} />
        <EnvBadge label="Wind" available={envAvailability.wind} />
        <EnvBadge label="Sea Ice" available={envAvailability.seaIce} />
      </div>
      {(!envAvailability.ocean || !envAvailability.wind || !envAvailability.seaIce) && (
        <p className="text-xs text-amber-400/80">Missing environmental data — prediction will safely fall back to Persistence.</p>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={isLoading || !apiConnected}
          className="flex-1 flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors">
          {isLoading ? (
            <><span className="animate-spin">⏳</span> Generating prediction...</>
          ) : (
            <><Send className="w-4 h-4" /> Generate Trajectory</>
          )}
        </button>
        <button type="button" onClick={handleReset}
          className="flex items-center gap-1 text-slate-400 hover:text-white border border-slate-600 hover:border-slate-500 rounded-lg px-3 py-2.5 text-sm transition-colors">
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs text-slate-400">{label}</span>
      {children}
      {error && <span className="text-xs text-red-400 mt-0.5 block">{error}</span>}
    </label>
  );
}

function EnvBadge({ label, available }: { label: string; available: boolean }) {
  return (
    <span className={`flex items-center gap-1 ${available ? 'text-emerald-400' : 'text-amber-400'}`}>
      <span className={`w-2 h-2 rounded-full ${available ? 'bg-emerald-400' : 'bg-amber-400'}`} />
      {label}
    </span>
  );
}
