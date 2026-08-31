# Phase 13 — Trajectory Frontend Documentation

## Objective

Build a standalone, integration-ready frontend dashboard for the Antarctic Iceberg Trajectory Prediction module. The frontend consumes the Phase 10 FastAPI inference API and visualizes trajectory predictions, model selection, prediction horizons, environmental conditions, and fallback status.

---

## Frontend Architecture

```
USER
  ↓
React + TypeScript UI (Vite)
  ↓
Trajectory API Client (Axios)
  ↓
FastAPI /predict/trajectory
  ↓
MultiHorizonPredictor → RegimeHybridPredictor
  ↓
Persistence / Physics B
  ↓
Predicted Coordinates × 5 horizons
```

The frontend **never** directly accesses PyTorch models, scalers, Parquet files, or internal physics equations. The API is the only boundary.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 |
| Language | TypeScript 6 |
| Build | Vite 8 |
| Styling | Tailwind CSS v4 |
| Map | React-Leaflet + Leaflet |
| Charts | Recharts |
| HTTP | Axios |
| Icons | Lucide React |
| Testing | Vitest + React Testing Library + jsdom |

---

## Component Structure

```
frontend/src/
├── api/
│   └── trajectoryApi.ts          # Isolated API client (checkHealth, getModelInfo, predictTrajectory)
├── components/
│   ├── Header.tsx                # Project identity + API/Model connection status
│   ├── IcebergSearch.tsx         # Observation input form + validation + Demo Mode
│   ├── TrajectoryMap.tsx         # Leaflet map with trajectory lines and horizon markers
│   ├── PredictionCards.tsx       # 5 forecast horizon cards with click-to-highlight
│   ├── ModelStatus.tsx           # Regime-Aware Hybrid engine display + routing rules
│   ├── EnvironmentPanel.tsx      # Ocean/Wind/Sea Ice availability and values
│   ├── FallbackAlert.tsx         # Degraded prediction warning banner
│   ├── ErrorChart.tsx            # Held-out test performance bar chart
│   └── Limitations.tsx           # Model limitations disclosure
├── hooks/
│   └── useTrajectoryPrediction.ts  # Custom hook: API state, prediction lifecycle, NaN rejection
├── pages/
│   └── TrajectoryDashboard.tsx   # Main 3-panel dashboard layout
├── types/
│   └── trajectory.ts             # TypeScript interfaces matching Pydantic schemas
├── utils/
│   └── coordinates.ts            # Coordinate validation & displacement calculation
└── __tests__/
    ├── coordinates.test.ts       # 20 tests — coordinate safety
    ├── api.test.ts               # 15 tests — API mocking, NaN detection, immutability
    └── components.test.tsx       # 37 tests — component rendering & edge cases
```

---

## API Integration

### Endpoints Consumed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Connection status & supported horizons |
| `/model/info` | GET | Model metadata (threshold, supported horizons) |
| `/predict/trajectory` | POST | Multi-horizon trajectory prediction |

### Configuration

```env
VITE_TRAJECTORY_API_URL=http://localhost:8000
```

CORS is enabled on the FastAPI backend (`allow_origins=["*"]`).

---

## UI Features

1. **Header**: Live API/Model connection status with colored indicators and last prediction timestamp.
2. **Observation Input**: Validated fields for iceberg ID, position, velocity, heading, and optional environmental inputs. Includes Demo Mode with pre-filled d27 sample data.
3. **Environment Availability**: Explicit green/amber badges for Ocean, Wind, Sea Ice availability. Missing data triggers a fallback warning message.
4. **Trajectory Map**: Dark CartoDB basemap centered on Antarctica. Current position marker + 5 colored forecast trajectory lines with toggle-able horizons and popups.
5. **Prediction Cards**: Five cards (24h, 72h, 168h, 240h, 720h) showing predicted lat/lon, displacement, selected model, and quality. Click highlights the trajectory on the map.
6. **Model Status Panel**: Displays "Regime-Aware Hybrid" label, current regime (MOVING/STATIONARY), routed model, velocity, and the `v < 0.03 → Persistence / v ≥ 0.03 → Physics B` routing rules.
7. **Fallback Alert**: Visible amber warning when `fallback_used=true`, explaining Persistence fallback and zero displacement.
8. **Error Chart**: Recharts bar chart showing the held-out test leaderboard (7 models). Clearly labeled "Held-Out Test Performance."
9. **Limitations Panel**: Concise disclosure of long-horizon uncertainty, high-velocity outliers, and model constraints.
10. **Loading/Error/Empty States**: Distinct overlays for idle, loading, error, and success states.

---

## Testing Strategy

### Test Files

| File | Tests | Category |
|------|-------|----------|
| `coordinates.test.ts` | 20 | Coordinate validation & displacement math |
| `api.test.ts` | 15 | API mocking, response parsing, NaN detection, immutability |
| `components.test.tsx` | 37 | Component rendering, edge cases, empty/fallback states |
| **Total** | **72** | |

### Test Coverage

- **Coordinate Safety**: Valid/invalid lat/lon, NaN, Infinity, displacement calculation, formatting.
- **API Mock Validation**: Health, model info, prediction with mocked responses. Server error propagation. Request/response immutability.
- **NaN/Infinity Rejection**: Explicit detection tests for NaN latitude, Infinity longitude, -Infinity displacement.
- **Component Rendering**: Header, PredictionCards, ModelStatus, FallbackAlert, EnvironmentPanel, TrajectoryMap, IcebergSearch.
- **Fallback/Degraded State**: FallbackAlert renders with correct count. Degraded quality badge displays. persistence_fallback model name shown.
- **Regime Behavior**: MOVING / STATIONARY / SLOW regime labels. 0.03 m/s threshold displayed. Physics B and Persistence model names correctly rendered. Frontend trusts API response — does NOT implement its own model selection.
- **Map Safety**: Renders with null predictions, empty arrays, valid Antarctic coordinates, and full 5-horizon predictions without crashing.

---

## Test Results

```
Frontend:  72/72 passed (3 test files)
TypeScript: 0 errors
Vite Build: SUCCESS (dist/ generated)
Backend:   118/118 passed (no regression)
```

---

## Coordinate Safety Validation

The `coordinates.ts` utility module provides the safety gates:

- `isValidLatitude`: Rejects NaN, Infinity, < -90, > 90.
- `isValidLongitude`: Rejects NaN, Infinity, < -180, > 180.
- `isFiniteCoord`: Rejects NaN and Infinity.
- The `useTrajectoryPrediction` hook validates every prediction coordinate for finiteness before setting state.

---

## Fallback/Degraded-State Behavior

When the API returns `fallback_used: true`:

1. `FallbackAlert` renders an amber warning banner stating "Degraded Prediction" with the count of affected horizons.
2. `PredictionCards` shows an amber "degraded" quality badge.
3. The `selected_model` field displays `persistence_fallback`.
4. Displacement shows 0 m/km (coordinates remain at observed position).
5. The dashboard **never** hides or suppresses this condition.

---

## Build Validation

```
Build command:  tsc && vite build
Output:
  dist/index.html         0.91 kB
  dist/assets/index.css  41.13 kB (gzip: 11.67 kB)
  dist/assets/index.js  790.48 kB (gzip: 241.46 kB)
Status: SUCCESS
```

---

## Known Limitations

1. **No Polar Projection**: Leaflet uses WGS84 (EPSG:4326). EPSG:3031 is not applied in the map for integration simplicity.
2. **No Live Confidence Intervals**: The model does not produce statistically calibrated confidence — the UI correctly avoids displaying fake confidence percentages.
3. **Map Canvas in Tests**: jsdom cannot render Leaflet canvas/WebGL, so map tests are structural (no-crash, legend presence) rather than visual.
4. **Single Bundle**: The production build is a single chunk (~790 kB). Code splitting can be added later.
5. **No Authentication**: No user auth — this is a standalone module for integration.

---

## Phase 13 Status

**COMPLETE**

| Gate | Result |
|------|--------|
| Frontend unit tests | 72/72 passed |
| TypeScript check | 0 errors |
| Vite production build | SUCCESS |
| Backend regression | 118/118 passed |
| No backend modifications | ✅ (only CORS middleware added) |
| No model/threshold changes | ✅ |
| API contract preserved | ✅ |
