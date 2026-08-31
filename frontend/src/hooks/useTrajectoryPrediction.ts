import { useState, useCallback, useRef, useEffect } from 'react';
import { checkHealth, getModelInfo, predictTrajectory } from '../api/trajectoryApi';
import type {
  TrajectoryRequest,
  TrajectoryResponse,
  HealthResponse,
  ModelInfoResponse,
  ConnectionStatus,
  PredictionState,
} from '../types/trajectory';

export function useTrajectoryPrediction() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('checking');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [predictionState, setPredictionState] = useState<PredictionState>('idle');
  const [response, setResponse] = useState<TrajectoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastPredictionTime, setLastPredictionTime] = useState<string | null>(null);
  const abortRef = useRef(false);

  const checkConnection = useCallback(async () => {
    setConnectionStatus('checking');
    try {
      const h = await checkHealth();
      setHealth(h);
      const m = await getModelInfo();
      setModelInfo(m);
      setConnectionStatus('connected');
    } catch {
      setConnectionStatus('disconnected');
      setHealth(null);
      setModelInfo(null);
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  const predict = useCallback(async (request: TrajectoryRequest) => {
    if (predictionState === 'loading') return;
    abortRef.current = false;
    setPredictionState('loading');
    setError(null);

    try {
      const res = await predictTrajectory(request);
      if (abortRef.current) return;

      // Validate response integrity
      for (const p of res.predictions) {
        if (!Number.isFinite(p.predicted_latitude) || !Number.isFinite(p.predicted_longitude)) {
          throw new Error('API returned non-finite coordinates');
        }
        if (!Number.isFinite(p.predicted_dx_m) || !Number.isFinite(p.predicted_dy_m)) {
          throw new Error('API returned non-finite displacement');
        }
      }

      setResponse(res);
      setPredictionState('success');
      setLastPredictionTime(new Date().toISOString());
    } catch (err: unknown) {
      if (abortRef.current) return;
      const msg =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred';
      setError(msg);
      setPredictionState('error');
    }
  }, [predictionState]);

  const reset = useCallback(() => {
    abortRef.current = true;
    setPredictionState('idle');
    setResponse(null);
    setError(null);
  }, []);

  return {
    connectionStatus,
    health,
    modelInfo,
    predictionState,
    response,
    error,
    lastPredictionTime,
    predict,
    reset,
    checkConnection,
  };
}
