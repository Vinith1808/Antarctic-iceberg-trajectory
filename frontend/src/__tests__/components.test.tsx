/**
 * Phase 13 — Component Rendering & Integration Tests
 *
 * Tests that all major UI components render correctly with mock data,
 * display the right model/horizon/fallback information, and handle
 * empty/error states gracefully.
 *
 * Uses jsdom — Leaflet map tests are structural (props/no-crash) since
 * jsdom cannot render canvas/WebGL.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import type { Prediction, ModelInfoResponse } from '../types/trajectory';

// ─── Shared fixtures ───────────────────────────────────────────────────────

function makePrediction(overrides: Partial<Prediction> = {}): Prediction {
  return {
    horizon_hours: 24,
    predicted_dx_m: 3000,
    predicted_dy_m: 4000,
    predicted_latitude: -66.1234,
    predicted_longitude: -60.4567,
    selected_model: 'Physics B',
    fallback_used: false,
    prediction_quality: 'nominal',
    ...overrides,
  };
}

const FIVE_PREDICTIONS: Prediction[] = [
  makePrediction({ horizon_hours: 24 }),
  makePrediction({ horizon_hours: 72 }),
  makePrediction({ horizon_hours: 168 }),
  makePrediction({ horizon_hours: 240 }),
  makePrediction({ horizon_hours: 720 }),
];

const MODEL_INFO: ModelInfoResponse = {
  model: 'regime_hybrid',
  low_speed_model: 'persistence',
  high_speed_model: 'physics_b',
  threshold_ms: 0.03,
  supported_horizons: [24, 72, 168, 240, 720],
};

// ─── Header ────────────────────────────────────────────────────────────────

import Header from '../components/Header';

describe('Header', () => {
  it('renders the project title', () => {
    render(<Header connectionStatus="connected" modelReady={true} lastPredictionTime={null} />);
    expect(screen.getByText('Antarctic Iceberg Trajectory Intelligence')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<Header connectionStatus="connected" modelReady={true} lastPredictionTime={null} />);
    expect(screen.getByText('Regime-Aware Hybrid Prediction Engine')).toBeInTheDocument();
  });

  it('shows API label', () => {
    render(<Header connectionStatus="connected" modelReady={true} lastPredictionTime={null} />);
    expect(screen.getByText('API')).toBeInTheDocument();
  });

  it('shows Model label', () => {
    render(<Header connectionStatus="disconnected" modelReady={false} lastPredictionTime={null} />);
    expect(screen.getByText('Model')).toBeInTheDocument();
  });
});

// ─── PredictionCards ───────────────────────────────────────────────────────

import PredictionCards from '../components/PredictionCards';

describe('PredictionCards', () => {
  it('renders exactly 5 horizon cards', () => {
    const onSelect = vi.fn();
    render(<PredictionCards predictions={FIVE_PREDICTIONS} activeHorizon={null} onSelectHorizon={onSelect} />);
    expect(screen.getByText('24h (1 day)')).toBeInTheDocument();
    expect(screen.getByText('72h (3 days)')).toBeInTheDocument();
    expect(screen.getByText('168h (1 week)')).toBeInTheDocument();
    expect(screen.getByText('240h (10 days)')).toBeInTheDocument();
    expect(screen.getByText('720h (30 days)')).toBeInTheDocument();
  });

  it('displays predicted latitude and longitude', () => {
    const onSelect = vi.fn();
    render(<PredictionCards predictions={[makePrediction()]} activeHorizon={null} onSelectHorizon={onSelect} />);
    expect(screen.getByText('-66.1234°')).toBeInTheDocument();
    expect(screen.getByText('-60.4567°')).toBeInTheDocument();
  });

  it('displays displacement in km', () => {
    const onSelect = vi.fn();
    // 3000² + 4000² = 5000m = 5.0 km
    render(<PredictionCards predictions={[makePrediction()]} activeHorizon={null} onSelectHorizon={onSelect} />);
    expect(screen.getByText('Δ 5.0 km')).toBeInTheDocument();
  });

  it('displays the selected model', () => {
    const onSelect = vi.fn();
    render(<PredictionCards predictions={[makePrediction({ selected_model: 'Physics B' })]} activeHorizon={null} onSelectHorizon={onSelect} />);
    expect(screen.getByText('Physics B')).toBeInTheDocument();
  });

  it('shows nominal quality for non-fallback predictions', () => {
    const onSelect = vi.fn();
    render(<PredictionCards predictions={[makePrediction({ prediction_quality: 'nominal', fallback_used: false })]} activeHorizon={null} onSelectHorizon={onSelect} />);
    expect(screen.getByText('nominal')).toBeInTheDocument();
  });

  it('shows degraded quality for fallback predictions', () => {
    const onSelect = vi.fn();
    render(
      <PredictionCards
        predictions={[makePrediction({ prediction_quality: 'degraded', fallback_used: true, selected_model: 'persistence_fallback' })]}
        activeHorizon={null}
        onSelectHorizon={onSelect}
      />
    );
    expect(screen.getByText('degraded')).toBeInTheDocument();
    expect(screen.getByText('persistence_fallback')).toBeInTheDocument();
  });

  it('displays Persistence for stationary iceberg predictions', () => {
    const onSelect = vi.fn();
    render(
      <PredictionCards
        predictions={[makePrediction({ selected_model: 'Persistence', predicted_dx_m: 0, predicted_dy_m: 0 })]}
        activeHorizon={null}
        onSelectHorizon={onSelect}
      />
    );
    expect(screen.getByText('Persistence')).toBeInTheDocument();
    expect(screen.getByText('Δ 0.0 km')).toBeInTheDocument();
  });
});

// ─── ModelStatus ───────────────────────────────────────────────────────────

import ModelStatus from '../components/ModelStatus';

describe('ModelStatus', () => {
  it('renders nothing when modelInfo is null', () => {
    const { container } = render(<ModelStatus modelInfo={null} velocity={0.05} selectedModel={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders Regime-Aware Hybrid label', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.05} selectedModel="Physics B" />);
    expect(screen.getByText('Regime-Aware Hybrid')).toBeInTheDocument();
  });

  it('shows MOVING regime for velocity >= 0.03', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.05} selectedModel="Physics B" />);
    expect(screen.getByText('MOVING')).toBeInTheDocument();
  });

  it('shows STATIONARY / SLOW regime for velocity < 0.03', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.01} selectedModel="Persistence" />);
    expect(screen.getByText('STATIONARY / SLOW')).toBeInTheDocument();
  });

  it('displays the 0.03 m/s threshold in routing rules', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.05} selectedModel="Physics B" />);
    const thresholdElements = screen.getAllByText(/0.03/);
    expect(thresholdElements.length).toBeGreaterThanOrEqual(1);
  });

  it('displays Physics B as selected model', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.05} selectedModel="Physics B" />);
    expect(screen.getByText('Physics B')).toBeInTheDocument();
  });

  it('displays velocity in m/s', () => {
    render(<ModelStatus modelInfo={MODEL_INFO} velocity={0.084} selectedModel="Physics B" />);
    expect(screen.getByText('0.0840 m/s')).toBeInTheDocument();
  });
});

// ─── FallbackAlert ─────────────────────────────────────────────────────────

import FallbackAlert from '../components/FallbackAlert';

describe('FallbackAlert', () => {
  it('renders nothing when predictions is null', () => {
    const { container } = render(<FallbackAlert predictions={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders nothing when no fallback used', () => {
    const { container } = render(
      <FallbackAlert predictions={[makePrediction({ fallback_used: false })]} />
    );
    expect(container.innerHTML).toBe('');
  });

  it('shows degraded alert when fallback is used', () => {
    render(
      <FallbackAlert predictions={[makePrediction({ fallback_used: true })]} />
    );
    expect(screen.getByText('Degraded Prediction')).toBeInTheDocument();
    expect(screen.getByText(/Persistence fallback/)).toBeInTheDocument();
  });

  it('reports correct fallback count', () => {
    const preds = [
      makePrediction({ horizon_hours: 24, fallback_used: true }),
      makePrediction({ horizon_hours: 72, fallback_used: true }),
      makePrediction({ horizon_hours: 168, fallback_used: false }),
    ];
    render(<FallbackAlert predictions={preds} />);
    expect(screen.getByText(/2 of 3 horizons/)).toBeInTheDocument();
  });
});

// ─── EnvironmentPanel ──────────────────────────────────────────────────────

import EnvironmentPanel from '../components/EnvironmentPanel';

describe('EnvironmentPanel', () => {
  it('renders Environmental State heading', () => {
    render(<EnvironmentPanel uo={0.03} vo={-0.02} u10={4.5} v10={-3.1} siconc={0.15} velocity={0.084} heading={225} />);
    expect(screen.getByText('Environmental State')).toBeInTheDocument();
  });

  it('shows ocean current values when provided', () => {
    render(<EnvironmentPanel uo={0.03} vo={-0.02} u10={null} v10={null} siconc={null} velocity={0.05} heading={180} />);
    expect(screen.getByText('U: 0.030')).toBeInTheDocument();
    expect(screen.getByText('V: -0.020')).toBeInTheDocument();
  });

  it('shows "Not provided" for missing ocean data', () => {
    render(<EnvironmentPanel uo={null} vo={null} u10={null} v10={null} siconc={null} velocity={0.05} heading={180} />);
    const notProvided = screen.getAllByText('Not provided');
    expect(notProvided.length).toBeGreaterThanOrEqual(3);
  });

  it('shows SIC percentage when provided', () => {
    render(<EnvironmentPanel uo={null} vo={null} u10={null} v10={null} siconc={0.75} velocity={0.05} heading={180} />);
    expect(screen.getByText('SIC: 75.0%')).toBeInTheDocument();
  });

  it('displays velocity and heading', () => {
    render(<EnvironmentPanel uo={null} vo={null} u10={null} v10={null} siconc={null} velocity={0.084} heading={225} />);
    expect(screen.getByText('Velocity: 0.0840 m/s')).toBeInTheDocument();
    expect(screen.getByText('Heading: 225.0°')).toBeInTheDocument();
  });
});

// ─── TrajectoryMap (structural, no canvas) ─────────────────────────────────

import TrajectoryMap from '../components/TrajectoryMap';

describe('TrajectoryMap', () => {
  it('renders without crashing with null predictions', () => {
    expect(() => render(
      <TrajectoryMap currentLat={null} currentLon={null} predictions={null} activeHorizon={null} />
    )).not.toThrow();
  });

  it('renders without crashing with valid Antarctic coordinates', () => {
    expect(() => render(
      <TrajectoryMap currentLat={-66.5} currentLon={-60.2} predictions={null} activeHorizon={null} />
    )).not.toThrow();
  });

  it('renders without crashing with predictions', () => {
    expect(() => render(
      <TrajectoryMap currentLat={-66.5} currentLon={-60.2} predictions={FIVE_PREDICTIONS} activeHorizon={24} />
    )).not.toThrow();
  });

  it('renders without crashing with empty prediction array', () => {
    expect(() => render(
      <TrajectoryMap currentLat={-66.5} currentLon={-60.2} predictions={[]} activeHorizon={null} />
    )).not.toThrow();
  });

  it('renders the horizon legend', () => {
    render(
      <TrajectoryMap currentLat={-66.5} currentLon={-60.2} predictions={FIVE_PREDICTIONS} activeHorizon={null} />
    );
    expect(screen.getByText('Forecast Horizons')).toBeInTheDocument();
  });
});

// ─── IcebergSearch (structural render) ─────────────────────────────────────

import IcebergSearch from '../components/IcebergSearch';

describe('IcebergSearch', () => {
  it('renders the observation input heading', () => {
    render(<IcebergSearch onSubmit={vi.fn()} onReset={vi.fn()} predictionState="idle" apiConnected={true} />);
    expect(screen.getByText('Observation Input')).toBeInTheDocument();
  });

  it('renders the Generate Trajectory button', () => {
    render(<IcebergSearch onSubmit={vi.fn()} onReset={vi.fn()} predictionState="idle" apiConnected={true} />);
    expect(screen.getByText('Generate Trajectory')).toBeInTheDocument();
  });

  it('shows loading state during prediction', () => {
    render(<IcebergSearch onSubmit={vi.fn()} onReset={vi.fn()} predictionState="loading" apiConnected={true} />);
    expect(screen.getByText('Generating prediction...')).toBeInTheDocument();
  });

  it('renders Demo Data button', () => {
    render(<IcebergSearch onSubmit={vi.fn()} onReset={vi.fn()} predictionState="idle" apiConnected={true} />);
    expect(screen.getByText('Demo Data')).toBeInTheDocument();
  });

  it('renders environmental input labels', () => {
    render(<IcebergSearch onSubmit={vi.fn()} onReset={vi.fn()} predictionState="idle" apiConnected={true} />);
    expect(screen.getByText(/Ocean U/)).toBeInTheDocument();
    expect(screen.getByText(/Wind U10/)).toBeInTheDocument();
    expect(screen.getByText(/Sea Ice Conc/)).toBeInTheDocument();
  });
});
