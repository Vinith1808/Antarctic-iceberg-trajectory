import { useState, useRef } from 'react';
import { useTrajectoryPrediction } from '../hooks/useTrajectoryPrediction';
import type { TrajectoryRequest } from '../types/trajectory';
import { displacementKm, formatCoord } from '../utils/coordinates';

import Header from '../components/Header';
import IcebergSearch from '../components/IcebergSearch';
import TrajectoryMap from '../components/TrajectoryMap';
import PredictionCards from '../components/PredictionCards';
import ModelStatus from '../components/ModelStatus';
import FallbackAlert from '../components/FallbackAlert';
import EnvironmentPanel from '../components/EnvironmentPanel';
import ErrorChart from '../components/ErrorChart';
import Limitations from '../components/Limitations';

import { MapPin, Navigation, Gauge, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function TrajectoryDashboard() {
  const {
    connectionStatus,
    health,
    modelInfo,
    predictionState,
    response,
    error,
    lastPredictionTime,
    predict,
    reset,
  } = useTrajectoryPrediction();

  const [activeHorizon, setActiveHorizon] = useState<number | null>(null);
  const lastRequestRef = useRef<TrajectoryRequest | null>(null);

  function handleSubmit(req: TrajectoryRequest) {
    lastRequestRef.current = req;
    setActiveHorizon(null);
    predict(req);
  }

  function handleReset() {
    lastRequestRef.current = null;
    setActiveHorizon(null);
    reset();
  }

  const currentLat = lastRequestRef.current?.latitude ?? null;
  const currentLon = lastRequestRef.current?.longitude ?? null;
  const predictions = response?.predictions ?? null;

  // Summary
  const maxDisp = predictions
    ? Math.max(...predictions.map(p => displacementKm(p.predicted_dx_m, p.predicted_dy_m)))
    : null;
  const primaryModel = predictions?.[0]?.selected_model ?? null;

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100">
      <Header
        connectionStatus={connectionStatus}
        modelReady={!!health}
        lastPredictionTime={lastPredictionTime}
      />

      <div className="flex-1 grid grid-cols-[360px_1fr_320px] gap-0 overflow-hidden">
        {/* LEFT PANEL — Input & Environment */}
        <aside className="border-r border-slate-800 overflow-y-auto p-4 space-y-4">
          <IcebergSearch
            onSubmit={handleSubmit}
            onReset={handleReset}
            predictionState={predictionState}
            apiConnected={connectionStatus === 'connected'}
          />

          {lastRequestRef.current && (
            <EnvironmentPanel
              uo={lastRequestRef.current.uo}
              vo={lastRequestRef.current.vo}
              u10={lastRequestRef.current.u10}
              v10={lastRequestRef.current.v10}
              siconc={lastRequestRef.current.siconc}
              velocity={lastRequestRef.current.velocity_ms}
              heading={lastRequestRef.current.heading_deg}
            />
          )}

          <ModelStatus
            modelInfo={modelInfo}
            velocity={lastRequestRef.current?.velocity_ms ?? 0}
            selectedModel={primaryModel}
          />
        </aside>

        {/* CENTER — Map */}
        <main className="relative overflow-hidden">
          {predictionState === 'idle' && !predictions && (
            <div className="absolute inset-0 flex items-center justify-center z-[500] pointer-events-none">
              <div className="text-center text-slate-500 space-y-2">
                <Navigation className="w-12 h-12 mx-auto opacity-30" />
                <p className="text-sm">No trajectory generated yet</p>
                <p className="text-xs">Enter iceberg observation and click Generate Trajectory</p>
              </div>
            </div>
          )}

          {predictionState === 'loading' && (
            <div className="absolute inset-0 flex items-center justify-center z-[500] bg-slate-950/50 backdrop-blur-sm">
              <div className="text-center text-cyan-400 space-y-2">
                <Clock className="w-10 h-10 mx-auto animate-pulse" />
                <p className="text-sm font-medium">Calculating iceberg trajectory...</p>
              </div>
            </div>
          )}

          {predictionState === 'error' && (
            <div className="absolute inset-0 flex items-center justify-center z-[500] pointer-events-none">
              <div className="text-center text-red-400 space-y-2 max-w-sm pointer-events-auto">
                <XCircle className="w-10 h-10 mx-auto" />
                <p className="text-sm font-medium">Trajectory service unavailable</p>
                <p className="text-xs text-red-300/70">{error}</p>
              </div>
            </div>
          )}

          <TrajectoryMap
            currentLat={currentLat}
            currentLon={currentLon}
            predictions={predictions}
            activeHorizon={activeHorizon}
          />
        </main>

        {/* RIGHT PANEL — Results & Analysis */}
        <aside className="border-l border-slate-800 overflow-y-auto p-4 space-y-4">
          {/* Status message */}
          {predictionState === 'success' && predictions && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-3 py-2 flex items-center gap-2 text-xs text-emerald-300">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              Trajectory generated successfully
            </div>
          )}

          <FallbackAlert predictions={predictions} />

          {/* Summary */}
          {predictions && currentLat != null && currentLon != null && (
            <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-4 space-y-2">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Trajectory Summary</h3>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                <span className="text-slate-500 flex items-center gap-1"><MapPin className="w-3 h-3" /> Position</span>
                <span className="text-white font-mono">{formatCoord(currentLat)}°, {formatCoord(currentLon)}°</span>
                <span className="text-slate-500">Range</span>
                <span className="text-white">24h → 720h</span>
                <span className="text-slate-500 flex items-center gap-1"><Gauge className="w-3 h-3" /> Max Δ</span>
                <span className="text-white font-mono">{maxDisp?.toFixed(1)} km</span>
                <span className="text-slate-500">Active Model</span>
                <span className="text-white">{primaryModel}</span>
                <span className="text-slate-500">State</span>
                <span className={predictions[0].fallback_used ? 'text-amber-400' : 'text-emerald-400'}>
                  {predictions[0].fallback_used ? 'Degraded' : 'Nominal'}
                </span>
              </div>
            </div>
          )}

          {/* Horizon cards */}
          {predictions && (
            <PredictionCards
              predictions={predictions}
              activeHorizon={activeHorizon}
              onSelectHorizon={h => setActiveHorizon(prev => prev === h ? null : h)}
            />
          )}

          {/* Error chart */}
          <ErrorChart />

          {/* Limitations */}
          <Limitations />
        </aside>
      </div>
    </div>
  );
}
