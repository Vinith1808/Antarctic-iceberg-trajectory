# Frontend Integration Guide

## Required Backend Endpoints

### `POST /predict/trajectory`
Primary prediction endpoint.

**Request Schema:**
```json
{
  "iceberg_id": "string (required)",
  "timestamp": "ISO 8601 datetime (required)",
  "latitude": "float, -90 to 90 (required)",
  "longitude": "float, -180 to 180 (required)",
  "velocity_ms": "float, >= 0 (required)",
  "heading_deg": "float (required)",
  "uo": "float or null (optional, ocean current u)",
  "vo": "float or null (optional, ocean current v)",
  "u10": "float or null (optional, 10m wind u)",
  "v10": "float or null (optional, 10m wind v)",
  "siconc": "float or null (optional, sea ice concentration 0-1)"
}
```

**Response Schema:**
```json
{
  "iceberg_id": "string",
  "input_timestamp": "ISO 8601 datetime",
  "predictions": [
    {
      "horizon_hours": 24.0,
      "predicted_dx_m": "float (EPSG:3031 meters)",
      "predicted_dy_m": "float (EPSG:3031 meters)",
      "predicted_latitude": "float",
      "predicted_longitude": "float",
      "selected_model": "string (Physics B | Persistence | persistence_fallback)",
      "fallback_used": "boolean",
      "prediction_quality": "string (nominal | degraded)"
    }
  ]
}
```

### `GET /health`
Returns API health status and supported horizons.

### `GET /model/info`
Returns deployed model metadata including the 0.03 m/s threshold.

## Environment Variable

```
VITE_TRAJECTORY_API_URL=http://localhost:8000
```

All API calls use this single configuration variable. Change it to point to any compatible backend.

## Integration Procedure

### 1. Copy the frontend module
```bash
cp -r frontend/ /path/to/your/project/iceberg-trajectory-ui/
```

### 2. Install dependencies
```bash
cd iceberg-trajectory-ui
npm install
```

### 3. Configure API URL
```bash
# Create .env file
echo "VITE_TRAJECTORY_API_URL=https://your-backend.example.com" > .env
```

### 4. Start the frontend
```bash
npm run dev
```

### 5. Connect to your backend
Ensure your backend implements the three endpoints above with CORS enabled.

### 6. Reuse individual components
Components are isolated and receive data via props:

```tsx
import TrajectoryMap from './components/TrajectoryMap';
import PredictionCards from './components/PredictionCards';

// Use inside your own React app
<TrajectoryMap
  currentLat={-65.0}
  currentLon={45.0}
  predictions={apiResponse.predictions}
  activeHorizon={24}
/>
```

## Component Props Reference

| Component | Key Props |
|-----------|-----------|
| `TrajectoryMap` | `currentLat`, `currentLon`, `predictions`, `activeHorizon` |
| `PredictionCards` | `predictions`, `activeHorizon`, `onSelectHorizon` |
| `ModelStatus` | `modelInfo`, `velocity`, `selectedModel` |
| `EnvironmentPanel` | `uo`, `vo`, `u10`, `v10`, `siconc`, `velocity`, `heading` |
| `FallbackAlert` | `predictions` |
| `ErrorChart` | (no props, uses static leaderboard data) |
