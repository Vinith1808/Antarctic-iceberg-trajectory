## 1. Kinematic Regime Robustness
### Stationary (<0.01)
- Sample count: 188
- Mean EPE: 1361.9 m
- Median EPE: 0.0 m
- P95 EPE: 6877.2 m
- % Persistence: 100.0%
- % Physics B: 0.0%

### Slow-moving (0.01-0.03)
- Sample count: 21
- Mean EPE: 26888.5 m
- Median EPE: 10471.8 m
- P95 EPE: 99316.9 m
- % Persistence: 100.0%
- % Physics B: 0.0%

### Moving (>=0.03)
- Sample count: 43
- Mean EPE: 57833.4 m
- Median EPE: 48850.4 m
- P95 EPE: 125189.6 m
- % Persistence: 0.0%
- % Physics B: 100.0%

## 2. Missing Environment Robustness
### Scenario A (All Available)
- Mean EPE: 13125.2 m
- Fallbacks: 0
- NaNs: 0
- Invalid Coords: 0

### Scenario B (No Ocean)
- Mean EPE: 17253.5 m
- Fallbacks: 36
- NaNs: 0
- Invalid Coords: 0

### Scenario C (No Wind)
- Mean EPE: 17090.0 m
- Fallbacks: 43
- NaNs: 0
- Invalid Coords: 0

### Scenario D (No Sea Ice)
- Mean EPE: 17253.5 m
- Fallbacks: 36
- NaNs: 0
- Invalid Coords: 0

### Scenario E (No Environment)
- Mean EPE: 17090.0 m
- Fallbacks: 43
- NaNs: 0
- Invalid Coords: 0

## 3. Prediction Horizon Robustness
### Short (<=168h)
- Sample Count: 103
- Mean EPE: 7316.2 m

### Medium (168-240h)
- Sample Count: 75
- Mean EPE: 12887.4 m

### Long (>240h)
- Sample Count: 74
- Mean EPE: 21451.6 m

## 4. Speed-Bin Analysis
### <0.01 m/s
- Sample Count: 188
- Mean EPE: 1361.9 m

### 0.01-0.03 m/s
- Sample Count: 21
- Mean EPE: 26888.5 m

### 0.03-0.10 m/s
- Sample Count: 30
- Mean EPE: 56430.6 m

### 0.10-0.30 m/s
- Sample Count: 13
- Mean EPE: 61070.8 m

### >=0.30 m/s
- Sample Count: 0
- Mean EPE: nan m

## 5. Physical Sanity Checks
1. No NaN predictions: True
2. No infinite predictions: True
3. Latitude in [-90, 90]: True
4. Longitude in [-180, 180]: True
5. Predicted displacement is consistent with coordinates: True (derived from projection)
6. Persistence preserves last position: True (dx, dy = 0)
7. Physics B uses existing params: True
8. Inputs not mutated: True
9. Missing env doesn't crash: True

## 6. Failure Case Analysis (Top 10 Errors)
- Iceberg: d27 | Horizon: 720.0h | Vel: 0.00m/s | EPE: 213.2km | Model: Physics B
- Iceberg: d27 | Horizon: 312.0h | Vel: 0.00m/s | EPE: 169.7km | Model: Physics B
- Iceberg: d30b | Horizon: 528.0h | Vel: 0.00m/s | EPE: 162.0km | Model: Persistence
- Iceberg: a81 | Horizon: 240.0h | Vel: 0.00m/s | EPE: 125.8km | Model: Physics B
- Iceberg: d27 | Horizon: 216.0h | Vel: 0.02m/s | EPE: 119.4km | Model: Physics B
- Iceberg: d27 | Horizon: 216.0h | Vel: 0.01m/s | EPE: 112.1km | Model: Physics B
- Iceberg: d27 | Horizon: 576.0h | Vel: 0.02m/s | EPE: 102.6km | Model: Physics B
- Iceberg: d27 | Horizon: 288.0h | Vel: 0.01m/s | EPE: 99.3km | Model: Persistence
- Iceberg: a81 | Horizon: 120.0h | Vel: 0.01m/s | EPE: 92.6km | Model: Physics B
- Iceberg: b46 | Horizon: 576.0h | Vel: 0.01m/s | EPE: 88.1km | Model: Physics B
## Phase 8.9.1 — Production Robustness Fix
**Vulnerability Discovered:** In Phase 8.9, forcing any required environmental covariate (ocean, wind, sea ice) to `NaN` caused the Physics B model to blindly propagate `NaN` into the trajectory predictions, breaking the "No NaN Predictions" rule.

**Root Cause:** The previous fallback rule in `regime_hybrid.py` incorrectly demanded that *all* environmental variables (`ocean`, `wind`, `iceberg_vel`) be `NaN` before triggering the safety fallback to Persistence. This permitted partial valid data (e.g. valid iceberg velocity but `NaN` wind) to attempt physical calculations.

**Corrected Rule:** The fallback logic was tightened. If *any* required environmental input (u/v components of ocean, wind, iceberg, or sea-ice concentration) is non-finite (`NaN` or `Inf`), the model immediately routes to `persistence_fallback`.

**Tests Added:** 10 explicit tests were added to `tests/test_regime_hybrid.py` verifying each missing environmental variable independently triggers the fallback, guaranteeing zero `NaN` coordinates and preserving original metadata.

**Before/After:**
- Before: Missing wind generated 43 `NaN` coordinate trajectories.
- After: Missing wind generated 0 `NaN` trajectories (all 43 routed to `persistence_fallback`).

**Production Guarantee:** The model architecture was NOT retrained. The 0.03 m/s routing policy remains absolutely unchanged. The model simply safely aborts to Persistence when its required inputs are corrupted.
