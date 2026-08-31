# Trajectory Inference API

## 1. API Purpose
The Trajectory Inference API provides an integration-ready HTTP wrapper around the frozen `MultiHorizonPredictor` and `RegimeHybridPredictor`. Its purpose is to securely and reliably serve multi-horizon predictions to the main Antarctic Navigation system without exposing underlying modeling infrastructure (PyTorch, SciKit-Learn, scalers) to external consumers.

**IMPORTANT NOTE**: This API exposes an already-validated trajectory model. It does **not** perform model training, parameter tuning, or modification of the underlying datasets.

## 2. Architecture
- **Framework**: FastAPI + Pydantic
- **Model Engine**: `MultiHorizonPredictor` -> `RegimeHybridPredictor` -> `Physics B` / `Persistence`
- **In-Memory Loading**: The predictor is instantiated once at startup and reused to ensure low-latency inference.
- **Fail-Safe Processing**: All incoming payloads are validated. Missing environmental fields correctly propagate to trigger the frozen Phase 8.9.1 Persistence fallback.

## 3. Endpoints

### `GET /health`
Validates that the API is responsive and the predictor is loaded in memory.
```json
{
  "status": "healthy",
  "service": "antarctic-iceberg-trajectory-predictor",
  "model": "regime_hybrid",
  "multi_horizon": true,
  "supported_horizons_hours": [24.0, 72.0, 168.0, 240.0, 720.0]
}
```

### `GET /model/info`
Exposes the deployed trajectory ruleset parameters.
```json
{
  "model": "regime_hybrid",
  "low_speed_model": "persistence",
  "high_speed_model": "physics_b",
  "threshold_ms": 0.03,
  "supported_horizons": [24.0, 72.0, 168.0, 240.0, 720.0]
}
```

### `POST /predict/trajectory`
Executes iceberg trajectory predictions for 5 standard horizons.

#### Request Schema
```json
{
  "iceberg_id": "d27",
  "timestamp": "2023-01-01T12:00:00Z",
  "latitude": -65.0,
  "longitude": 45.0,
  "velocity_ms": 0.05,
  "heading_deg": 180.0,
  "uo": 0.1,
  "vo": -0.1,
  "u10": 5.0,
  "v10": -5.0,
  "siconc": 0.5
}
```
*Note: `uo`, `vo`, `u10`, `v10`, and `siconc` may be omitted (or set to `null`).*

#### Response Schema
```json
{
  "iceberg_id": "d27",
  "input_timestamp": "2023-01-01T12:00:00Z",
  "predictions": [
    {
      "horizon_hours": 24.0,
      "predicted_dx_m": 1234.5,
      "predicted_dy_m": -4321.0,
      "predicted_latitude": -65.03,
      "predicted_longitude": 45.01,
      "selected_model": "Physics B",
      "fallback_used": false,
      "prediction_quality": "nominal"
    },
    ... (returns 5 horizons total)
  ]
}
```

## 4. Regime Selection Policy
The API inherits the strict, immutable Phase 8 routing policy:
- **velocity < 0.03 m/s** → `Persistence`
- **velocity >= 0.03 m/s** → `Physics Model B`

## 5. Missing-Data & Error Handling
- **Non-Finite Inputs**: If the API receives `NaN` / `null` for `uo`, `vo`, `u10`, `v10`, or `siconc`, it will safely abort the physical simulation and route the prediction to `persistence_fallback`. The `fallback_used` field will be `true`, and `prediction_quality` will be `degraded`.
- **Validation**: Latitudes outside [-90, 90], negative velocities, or non-numeric types are immediately rejected by FastAPI (HTTP 422).

## 6. Local Execution Command
To start the API locally:
```bash
uvicorn src.api.trajectory_api:app --reload
```

## 7. Integration Instructions
The main Antarctic system can consume this API cleanly:
1. Make a `POST` request containing iceberg attributes to `/predict/trajectory`.
2. Do not handle model switching or edge cases (the API does this internally).
3. If `fallback_used` is `true`, it means the API detected corrupt/missing environmental inputs and executed a zero-displacement fallback.
