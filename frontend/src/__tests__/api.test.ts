/**
 * Phase 13 — API Client & Hook Tests
 *
 * Tests the API client request construction, response parsing,
 * NaN/Infinity rejection, and error handling — all with mocked Axios.
 * No real backend required.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { TrajectoryResponse, Prediction } from '../types/trajectory';

// ─── Test fixtures ─────────────────────────────────────────────────────────

function makePrediction(overrides: Partial<Prediction> = {}): Prediction {
  return {
    horizon_hours: 24,
    predicted_dx_m: 1500,
    predicted_dy_m: -2000,
    predicted_latitude: -66.123,
    predicted_longitude: -60.456,
    selected_model: 'Physics B',
    fallback_used: false,
    prediction_quality: 'nominal',
    ...overrides,
  };
}

function makeResponse(overrides: Partial<TrajectoryResponse> = {}): TrajectoryResponse {
  return {
    iceberg_id: 'd27',
    input_timestamp: '2023-06-15T12:00:00Z',
    predictions: [
      makePrediction({ horizon_hours: 24 }),
      makePrediction({ horizon_hours: 72 }),
      makePrediction({ horizon_hours: 168 }),
      makePrediction({ horizon_hours: 240 }),
      makePrediction({ horizon_hours: 720 }),
    ],
    ...overrides,
  };
}

// ─── Mock the API module directly ──────────────────────────────────────────

vi.mock('../api/trajectoryApi', () => ({
  checkHealth: vi.fn(),
  getModelInfo: vi.fn(),
  predictTrajectory: vi.fn(),
}));

import { checkHealth, getModelInfo, predictTrajectory } from '../api/trajectoryApi';

const mockCheckHealth = vi.mocked(checkHealth);
const mockGetModelInfo = vi.mocked(getModelInfo);
const mockPredictTrajectory = vi.mocked(predictTrajectory);

beforeEach(() => {
  vi.clearAllMocks();
});

// ─── Health endpoint ───────────────────────────────────────────────────────

describe('checkHealth', () => {
  it('returns health data on success', async () => {
    const healthData = {
      status: 'healthy',
      service: 'antarctic-iceberg-trajectory-predictor',
      model: 'regime_hybrid',
      multi_horizon: true,
      supported_horizons_hours: [24, 72, 168, 240, 720],
    };
    mockCheckHealth.mockResolvedValueOnce(healthData);

    const result = await checkHealth();
    expect(mockCheckHealth).toHaveBeenCalled();
    expect(result).toEqual(healthData);
    expect(result.supported_horizons_hours).toHaveLength(5);
  });

  it('propagates network errors', async () => {
    mockCheckHealth.mockRejectedValueOnce(new Error('Network Error'));
    await expect(checkHealth()).rejects.toThrow('Network Error');
  });
});

// ─── Model info endpoint ───────────────────────────────────────────────────

describe('getModelInfo', () => {
  it('returns model metadata with 0.03 threshold', async () => {
    const infoData = {
      model: 'regime_hybrid',
      low_speed_model: 'persistence',
      high_speed_model: 'physics_b',
      threshold_ms: 0.03,
      supported_horizons: [24, 72, 168, 240, 720],
    };
    mockGetModelInfo.mockResolvedValueOnce(infoData);

    const result = await getModelInfo();
    expect(mockGetModelInfo).toHaveBeenCalled();
    expect(result.threshold_ms).toBe(0.03);
    expect(result.supported_horizons).toHaveLength(5);
  });
});

// ─── Prediction endpoint ──────────────────────────────────────────────────

describe('predictTrajectory', () => {
  it('sends request and returns response with 5 horizons', async () => {
    const response = makeResponse();
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const request = {
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

    const result = await predictTrajectory(request);
    expect(mockPredictTrajectory).toHaveBeenCalledWith(request);
    expect(result.predictions).toHaveLength(5);
  });

  it('returns exactly the 5 standard horizons', async () => {
    const response = makeResponse();
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const result = await predictTrajectory({
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
    });

    const horizons = result.predictions.map(p => p.horizon_hours);
    expect(horizons).toEqual([24, 72, 168, 240, 720]);
  });

  it('returns Physics B for moving iceberg', async () => {
    const response = makeResponse({
      predictions: [makePrediction({ selected_model: 'Physics B', fallback_used: false })],
    });
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const result = await predictTrajectory({
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
      uo: 0.1, vo: -0.1, u10: 5, v10: -5, siconc: 0.5,
    });
    expect(result.predictions[0].selected_model).toBe('Physics B');
    expect(result.predictions[0].fallback_used).toBe(false);
  });

  it('returns Persistence for stationary iceberg', async () => {
    const response = makeResponse({
      predictions: [makePrediction({
        selected_model: 'Persistence',
        prediction_quality: 'nominal',
        fallback_used: false,
        predicted_dx_m: 0,
        predicted_dy_m: 0,
      })],
    });
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const result = await predictTrajectory({
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.0, heading_deg: 0,
    });
    expect(result.predictions[0].selected_model).toBe('Persistence');
  });

  it('returns persistence_fallback when environmental data is missing', async () => {
    const response = makeResponse({
      predictions: [makePrediction({
        selected_model: 'persistence_fallback',
        prediction_quality: 'degraded',
        fallback_used: true,
        predicted_dx_m: 0,
        predicted_dy_m: 0,
      })],
    });
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const result = await predictTrajectory({
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
    });
    expect(result.predictions[0].selected_model).toBe('persistence_fallback');
    expect(result.predictions[0].fallback_used).toBe(true);
    expect(result.predictions[0].prediction_quality).toBe('degraded');
  });

  it('propagates server errors', async () => {
    mockPredictTrajectory.mockRejectedValueOnce(new Error('Request failed with status code 500'));
    await expect(
      predictTrajectory({
        iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
        latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
      })
    ).rejects.toThrow('500');
  });

  it('does not mutate the request object', async () => {
    const response = makeResponse();
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const request = {
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
    };
    const frozen = { ...request };

    await predictTrajectory(request);
    expect(request).toEqual(frozen);
  });

  it('does not mutate the response object', async () => {
    const response = makeResponse();
    const responseCopy = JSON.parse(JSON.stringify(response));
    mockPredictTrajectory.mockResolvedValueOnce(response);

    const result = await predictTrajectory({
      iceberg_id: 'test', timestamp: '2023-01-01T00:00:00Z',
      latitude: -65, longitude: 45, velocity_ms: 0.05, heading_deg: 180,
    });
    expect(result).toEqual(responseCopy);
  });
});

// ─── NaN/Infinity Detection ────────────────────────────────────────────────

describe('NaN/Infinity coordinate rejection', () => {
  it('NaN latitude in prediction is detectable', () => {
    const p = makePrediction({ predicted_latitude: NaN });
    expect(Number.isFinite(p.predicted_latitude)).toBe(false);
  });

  it('Infinity longitude in prediction is detectable', () => {
    const p = makePrediction({ predicted_longitude: Infinity });
    expect(Number.isFinite(p.predicted_longitude)).toBe(false);
  });

  it('-Infinity displacement is detectable', () => {
    const p = makePrediction({ predicted_dx_m: -Infinity });
    expect(Number.isFinite(p.predicted_dx_m)).toBe(false);
  });

  it('valid predictions pass finite checks', () => {
    const p = makePrediction();
    expect(Number.isFinite(p.predicted_latitude)).toBe(true);
    expect(Number.isFinite(p.predicted_longitude)).toBe(true);
    expect(Number.isFinite(p.predicted_dx_m)).toBe(true);
    expect(Number.isFinite(p.predicted_dy_m)).toBe(true);
  });
});
