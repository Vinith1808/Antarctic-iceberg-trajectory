# Phase 8.2: Data Split Strategy

## 1. Split Methodology
* **Method:** Grouped Iceberg-level Split (Leakage-Safe)
* **Random Seed:** 42
* **Reasoning:** Randomly splitting rows would leak future trajectory data of an iceberg into the training set, allowing the model to "cheat" by seeing the iceberg's future state. By splitting on `iceberg_id`, the model must generalize to completely unseen icebergs.

## 2. Split Distribution
* **Training Set:** 77 icebergs, 1878 observations
* **Validation Set:** 16 icebergs, 318 observations
* **Test Set:** 17 icebergs, 513 observations
* **Total Accounted:** 2709 observations (Expected: 2709)

## 3. Intersection Verification
* `TRAIN ∩ VALIDATION`: Empty
* `TRAIN ∩ TEST`: Empty
* `VALIDATION ∩ TEST`: Empty

## 4. Candidate Features
* **Base Trajectory:** `latitude`, `longitude`, `velocity_ms`, `heading_deg`, `distance_m`
* **Ocean:** `uo`, `vo`, `current_speed_ms`, `current_direction_deg`
* **Wind:** `u10`, `v10`, `wind_speed_ms`, `wind_direction_deg`
* **Sea Ice:** `siconc`
* **Time:** `time_since_previous_observation_hours`, `month`, `day_of_year`
* **Availability Masks:** `current_available`, `wind_available`, `seaice_available`

## 5. Candidate Target Definition
**Recommendation: OPTION C - Projected displacement in meters (Delta X / Delta Y)**

*Analysis:*
- **Option A (Next Lat/Lon):** Poor choice. Neural networks struggle to predict small variations in global coordinate spaces. Loss gradients will be dominated by the absolute magnitude rather than the movement.
- **Option B (Delta Lat/Lon):** Better, but degree sizes vary depending on latitude (1 degree longitude at -75 is physically much smaller than at the equator). This introduces spatial distortion.
- **Option C (Projected Displacement X/Y in meters):** **BEST.** This represents physical movement distance. It is scale-invariant and directly correlates with velocity and environmental forcing vectors.
- **Option D (Future Velocity/Heading):** Good for analysis, but heading wraps at 360 degrees, which creates discontinuous loss surfaces (e.g. 359 vs 1 degree).

*Handling Irregular Gaps:* Since the observation gap varies, predicting absolute displacement over `dt` is harder than predicting the continuous velocity vector (Vx, Vy). However, predicting displacement divided by `time_since_next_observation` (which is effectively velocity) normalizes the target.

## 6. Normalization Plan
* **Strategy:** Standard Scaling (Zero mean, unit variance)
* **Execution:** A scaler will be fit **ONLY on the Training Set**.
* **Transformation:** Validation and Test sets will be transformed using the fitted training scaler parameters to strictly prevent data leakage.
* **Features to Scale:** Environmental vectors (`u10`, `v10`, `uo`, `vo`), trajectory vectors (`velocity_ms`), and time gaps. Bounded features like `siconc` ([0,1]) and cyclic features (`month`, `day_of_year`, `heading`) will require min-max scaling or sine/cosine encodings, rather than standard scaling.

## 7. Recommendation for Phase 8.3
* Proceed to target generation (calculating future displacement) and sequence generation (creating sliding windows of length $N$). 
* Apply the normalization scalers explicitly fitted on `train.parquet`.
