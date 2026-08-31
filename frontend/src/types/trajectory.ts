// Types matching the Phase 10 Pydantic schemas exactly

export interface TrajectoryRequest {
  iceberg_id: string;
  timestamp: string; // ISO 8601
  latitude: number;
  longitude: number;
  velocity_ms: number;
  heading_deg: number;
  uo?: number | null;
  vo?: number | null;
  u10?: number | null;
  v10?: number | null;
  siconc?: number | null;
}

export interface Prediction {
  horizon_hours: number;
  predicted_dx_m: number;
  predicted_dy_m: number;
  predicted_latitude: number;
  predicted_longitude: number;
  selected_model: string;
  fallback_used: boolean;
  prediction_quality: string;
}

export interface TrajectoryResponse {
  iceberg_id: string;
  input_timestamp: string;
  predictions: Prediction[];
}

export interface HealthResponse {
  status: string;
  service: string;
  model: string;
  multi_horizon: boolean;
  supported_horizons_hours: number[];
}

export interface ModelInfoResponse {
  model: string;
  low_speed_model: string;
  high_speed_model: string;
  threshold_ms: number;
  supported_horizons: number[];
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'checking';
export type PredictionState = 'idle' | 'loading' | 'success' | 'error';

export interface EnvironmentAvailability {
  ocean: boolean;
  wind: boolean;
  seaIce: boolean;
}

export const HORIZON_COLORS: Record<number, string> = {
  24: '#22d3ee',   // cyan
  72: '#facc15',   // yellow
  168: '#f97316',  // orange
  240: '#ef4444',  // red
  720: '#a855f7',  // purple
};

export const HORIZON_LABELS: Record<number, string> = {
  24: '24h (1 day)',
  72: '72h (3 days)',
  168: '168h (1 week)',
  240: '240h (10 days)',
  720: '720h (30 days)',
};

export const MODEL_LEADERBOARD = [
  { model: 'Regime Hybrid', epe_km: 13.125 },
  { model: 'Physics B', epe_km: 14.280 },
  { model: 'Constant Velocity', epe_km: 15.101 },
  { model: 'Physics A', epe_km: 15.855 },
  { model: 'Persistence', epe_km: 17.090 },
  { model: 'Vanilla LSTM', epe_km: 19.234 },
  { model: 'Physics + Residual LSTM', epe_km: 19.535 },
];
