# Phase 8.3: Trajectory Sequence Generation

## 1. Prediction Problem Definition
* **Input:** A sequence of 10 historical trajectory and environmental observations.
* **Target:** Future iceberg displacement (`target_dx_m`, `target_dy_m`) from the last sequence observation to the next valid observation.
* **Target Coordinates:** EPSG:3031 (Antarctic Polar Stereographic). This CRS preserves distances accurately in the Antarctic region, making Euclidean target displacements mathematically sound and scale-invariant. The original lat/lon were retained as features without overwriting.

## 2. Sequence Length Analysis
*Candidate Evaluation on Train Split (Max Gap = 72h):*

|   seq_len |   usable_seqs |   pct_obs |   median_duration |   min_duration |   max_duration |
|----------:|--------------:|----------:|------------------:|---------------:|---------------:|
|         5 |          1257 |   66.9329 |               744 |            360 |           2016 |
|        10 |           915 |   48.722  |              1848 |           1056 |           3840 |
|        15 |           618 |   32.9073 |              3024 |           1944 |           4704 |
|        20 |           353 |   18.7966 |              3960 |           2784 |           5976 |

**Decision: sequence_length = 10**
*Reasoning:* Length 10 retains a high number of sequences while providing a median history of ~10 days (240 hours). Longer sequences drastically drop the number of available samples due to the irregular nature of iceberg tracking (fragmentation limits track lengths).

## 3. Gap & Missingness Thresholds
* **Max Temporal Gap:** 720 hours between any two consecutive points. Gaps exceeding this imply disconnected trajectories, so sequences crossing these gaps are discarded.
* **Max Missing Environmental Data:** 50.0%. Sequences with majority missing data (e.g., completely out of coverage) are discarded. 

## 4. Input Features
* **Scaled Features:** `latitude`, `longitude`, `velocity_ms`, `heading_deg`, `distance_m`, `uo`, `vo`, `current_speed_ms`, `current_direction_deg`, `u10`, `v10`, `wind_speed_ms`, `wind_direction_deg`, `siconc`, `time_since_previous_observation_hours`
* **Unscaled Cyclic Features:** `month_sin`, `month_cos`, `day_of_year_sin`, `day_of_year_cos`
* **Unscaled Availability Flags:** `current_available`, `wind_available`, `seaice_available`
* *Note:* Future targets/states are strictly excluded.

## 5. Target Analysis
* **Target Definition:** Projected spatial displacement vector `[target_dx_m, target_dy_m]` to the next chronological observation.
* **Magnitude Distribution (Train):** 
  * Min: 0.00m
  * Median: 2088.44m
  * Max: 652337.63m
  * Note: We retain extreme target outliers for robust sequence testing, reporting them here but not manually deleting them yet.

## 6. Output Dataset Statistics
* **Train Sequences:** 810
* **Validation Sequences:** 151
* **Test Sequences:** 252
* **Output Format:** NPZ archives for dense tensors (`X`: [N, 10, 22], `y`: [N, 2]) accompanied by Parquet metadata tables tracking `iceberg_id` and strict timestamps.

## 7. Scaling Strategy
* A `StandardScaler` was fit strictly on `train.npz` tensors (for non-categorical/non-cyclic features).
* Validation and test tensors were safely transformed using the train scaler.
* The scaler is serialized to `models/preprocessing/scaler.pkl`.

## 8. Leakage Verification
* Zero sequences cross train/val/test boundaries.
* Target timestamps are rigorously verified to be strictly *after* the sequence end timestamps.
* No future environmental parameters are used.

## 9. Next Steps (Phase 8.4)
Ready for PyTorch Dataset construction and baseline model (e.g. LSTM/Transformer) implementations using the verified NPZ sequences.
