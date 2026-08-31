import axios from 'axios';
import type {
  TrajectoryRequest,
  TrajectoryResponse,
  HealthResponse,
  ModelInfoResponse,
} from '../types/trajectory';

const API_BASE = import.meta.env.VITE_TRAJECTORY_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await client.get<HealthResponse>('/health');
  return data;
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const { data } = await client.get<ModelInfoResponse>('/model/info');
  return data;
}

export async function predictTrajectory(
  request: TrajectoryRequest
): Promise<TrajectoryResponse> {
  const { data } = await client.post<TrajectoryResponse>(
    '/predict/trajectory',
    request
  );
  return data;
}
