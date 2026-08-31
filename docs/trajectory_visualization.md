# Trajectory Visualization & Mapping (Phase 11)

## 1. Visualization Architecture
The visualization module (`src/visualization/`) provides geographic rendering and analysis plotting capabilities for the trajectory prediction pipeline. It relies entirely on the frozen Phase 10 API logic and Phase 9 Multi-Horizon Predictor. **It does not modify, retrain, or mutate any prediction logic, datasets, or scalers.**

The visualization logic is split into:
- `polar_map.py`: Core geographic mapping utilities (WGS84 -> EPSG:3031 projection, plotting standard elements like historical trails, ground truth, and predicted vectors).
- `trajectory_plots.py`: Orchestration script to run specific iceberg test cases through the `MultiHorizonPredictor` and generate figure images.
- `evaluation_plots.py`: (Pre-existing/Reused) Generates scatter/line plots for aggregate errors based on CSV artifacts.

## 2. Coordinate Systems & Antarctic Projection
All plotting of geographic locations is done natively in **EPSG:3031 (Antarctic Polar Stereographic)**.
The model processes and outputs standard WGS84 (`EPSG:4326`) latitude and longitude. The visualization tools explicitly project these WGS84 coordinates into Cartesian `x, y` meters (EPSG:3031) immediately prior to passing them into `matplotlib` to ensure true distances and angles are preserved visually.

*Crucial rule*: This coordinate transformation is strictly read-only for visualization. The underlying datasets and prediction tensors are never overwritten.

## 3. Visualized Plot Types
The system produces several primary plotting modes:

### 3.1 Historical & Predicted Trajectories
Plots displaying the 10-day historical window (grey line), current position (black square), ground truth path (green star), and predicted future path (red/colored cross).

### 3.2 Five-Horizon Forecast Maps
Visualizes a single iceberg with the Multi-Horizon Predictor's output for all 5 intervals (24h, 72h, 168h, 240h, 720h) simultaneously. Each horizon uses the frozen Phase 10 inference engine, ensuring predictions are consistent with deployment expectations.

### 3.3 Model Trajectory Comparison
Generates side-by-side or combined trajectory paths comparing the independent forecasts from:
- Persistence (Zero-displacement)
- Physics Model B (Wind/Ocean vector driven)
- Regime-Aware Hybrid Predictor (Velocity-gated)

## 4. Representative Test Cases
To provide robust validation, visualization automatically tests the boundary states of the model using representative cases identified directly from `test_meta.parquet`.
1. **Stationary**: (Velocity < 0.01 m/s)
2. **Slow-Moving**: (0.01 <= Velocity < 0.03 m/s)
3. **Actively Moving**: (Velocity >= 0.03 m/s)
4. **Outlier**: (`iceberg_id == 'd27'`)

## 5. Limitations & Constraints
1. **No Basemap Vector Data**: The mapping currently generates Cartesian grid axes over EPSG:3031 space but omits complex Antarctica coastline shapefiles to minimize dependency bloat (avoiding Cartopy/Geodatasets installation). The focus is entirely on the geometry of the trajectory relative to itself.
2. **Read-Only**: Generating plots will not trigger missing-data imputation or model retraining. Missing predictions safely fall back to the origin per Phase 8.9.1.
3. **Discrete Output**: The forecast plots connect discrete intervals (e.g. 72h to 168h). We do not apply cubic-spline interpolation between horizons, preserving exactly what the model predicts.
