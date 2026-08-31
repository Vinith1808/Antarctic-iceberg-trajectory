# Phase 8.1: Unified Modeling Dataset Report

## 1. Input Dataset Summary

### iceberg_motion.parquet
- **Row count:** 2709
- **Columns:** iceberg_id, timestamp, latitude, longitude, x_m, y_m, observation_index, time_since_previous_observation_hours, delta_x_m, delta_y_m, distance_m, velocity_ms, velocity_kmh, heading_deg, motion_quality_flag
- **Unique icebergs:** 110
- **Timestamp range:** 2020-12-31 00:00:00 to 2026-08-16 00:00:00
- **Duplicates (id+time):** 0
- **Missing values:**
  - `time_since_previous_observation_hours`: 110
  - `delta_x_m`: 110
  - `delta_y_m`: 110
  - `distance_m`: 110
  - `velocity_ms`: 110
  - `velocity_kmh`: 110
  - `heading_deg`: 1165
- **Latitude range:** [-77.48, 0.00]
- **Longitude range:** [-179.90, 179.97]
- **Is iceberg_id + timestamp a unique identifier?** True

### iceberg_currents.parquet
- **Row count:** 2707
- **Columns:** iceberg_id, timestamp, latitude, longitude, uo, vo, current_speed_ms, current_direction_deg, copernicus_timestamp, copernicus_latitude, copernicus_longitude, surface_depth_m, current_quality_flag
- **Unique icebergs:** 110
- **Timestamp range:** 2020-12-31 00:00:00 to 2026-08-16 00:00:00
- **Duplicates (id+time):** 0
- **Missing values:**
  - `uo`: 489
  - `vo`: 489
  - `current_speed_ms`: 489
  - `current_direction_deg`: 489
  - `copernicus_timestamp`: 261
  - `copernicus_latitude`: 261
  - `copernicus_longitude`: 261
- **Latitude range:** [-77.48, 0.00]
- **Longitude range:** [-179.90, 179.97]
- **Is iceberg_id + timestamp a unique identifier?** True

### iceberg_wind.parquet
- **Row count:** 2709
- **Columns:** iceberg_id, timestamp, latitude, longitude, u10, v10, wind_speed_ms, wind_direction_deg, era5_timestamp, era5_latitude, era5_longitude, wind_quality_flag
- **Unique icebergs:** 110
- **Timestamp range:** 2020-12-31 00:00:00 to 2026-08-16 00:00:00
- **Duplicates (id+time):** 0
- **Missing values:**
  - None
- **Latitude range:** [-77.48, 0.00]
- **Longitude range:** [-179.90, 179.97]
- **Is iceberg_id + timestamp a unique identifier?** True

### iceberg_seaice.parquet
- **Row count:** 2709
- **Columns:** iceberg_id, timestamp, latitude, longitude, siconc, cmems_timestamp, cmems_latitude, cmems_longitude, seaice_quality_flag
- **Unique icebergs:** 110
- **Timestamp range:** 2020-12-31 00:00:00 to 2026-08-16 00:00:00
- **Duplicates (id+time):** 0
- **Missing values:**
  - `siconc`: 930
  - `cmems_timestamp`: 299
  - `cmems_latitude`: 299
  - `cmems_longitude`: 299
- **Latitude range:** [-77.48, 0.00]
- **Longitude range:** [-179.90, 179.97]
- **Is iceberg_id + timestamp a unique identifier?** True

## 2. Merge Strategy
* **Primary Join Key:** `iceberg_id` + `timestamp`
* **Join Type:** LEFT JOIN starting from `iceberg_motion.parquet`.
* **Coordinate Handling:** Coordinates (`latitude`, `longitude`) are strictly taken from the authoritative motion dataset. Environmental coordinates were dropped to prevent leakage/duplication.

## 3. Final Schema
* **Total Columns:** 31
* **Columns:** iceberg_id, timestamp, latitude, longitude, distance_m, velocity_ms, velocity_kmh, heading_deg, motion_quality_flag, time_since_previous_observation_hours, uo, vo, current_speed_ms, current_direction_deg, current_quality_flag, u10, v10, wind_speed_ms, wind_direction_deg, wind_quality_flag, siconc, seaice_quality_flag, year, month, day_of_year, day_of_week, hour, days_since_previous_observation, current_available, wind_available, seaice_available

## 4. Row Preservation Results
* **Expected Rows:** 2709
* **Actual Merged Rows:** 2709
* **Expected Unique Icebergs:** 110
* **Actual Unique Icebergs:** 110
* **Rows increased due to merge?** No (PASS)

## 5. Duplicate Analysis
* **Duplicates in merged dataset (`iceberg_id` + `timestamp`):** 0

## 6. Missing-value Analysis
- **uo**: Missing: 491 (18.12%), Valid: 2218, Min: -0.6757, Max: 0.6043, Mean: -0.0402, Median: -0.0281
- **vo**: Missing: 491 (18.12%), Valid: 2218, Min: -0.5383, Max: 0.4089, Mean: 0.0012, Median: 0.0040
- **current_speed_ms**: Missing: 491 (18.12%), Valid: 2218, Min: 0.0006, Max: 0.7642, Mean: 0.1002, Median: 0.0758
- **current_direction_deg**: Missing: 491 (18.12%), Valid: 2218, Min: 0.0000, Max: 359.4838, Mean: 212.9907, Median: 238.2370
- **u10**: Missing: 0 (0.00%), Valid: 2709, Min: -29.0785, Max: 16.4331, Mean: -1.9848, Median: -2.0247
- **v10**: Missing: 0 (0.00%), Valid: 2709, Min: -15.7876, Max: 20.3580, Mean: 1.6159, Median: 1.7817
- **wind_speed_ms**: Missing: 0 (0.00%), Valid: 2709, Min: 0.2062, Max: 29.5144, Mean: 7.6968, Median: 6.9435
- **wind_direction_deg**: Missing: 0 (0.00%), Valid: 2709, Min: 0.0041, Max: 359.9665, Mean: 202.2653, Median: 252.9343
- **siconc**: Missing: 930 (34.33%), Valid: 1779, Min: 0.0000, Max: 1.0000, Mean: 0.7298, Median: 0.8710

## 7. Environmental Availability Combinations
- **All three available**: 1779
- **Current only**: 0
- **Wind only**: 526
- **Sea ice only**: 0
- **Current + Wind (no ice)**: 404
- **Current + Sea ice (no wind)**: 0
- **Wind + Sea ice (no current)**: 0
- **None available**: 0

## 8. Coordinate Integrity Checks
* **Latitude match:** Confirmed strictly identical to `iceberg_motion.parquet`.
* **Longitude match:** Confirmed strictly identical to `iceberg_motion.parquet`.

## 9. Temporal Integrity Checks
* **Timestamps unchanged:** Yes, derived directly from `iceberg_motion.parquet`.
* **Chronological Ordering:** Confirmed. The dataset is sorted by `iceberg_id` and `timestamp`.

## 10. Data-Quality Concerns Discovered
* Environmental variables have missing data primarily driven by out-of-bounds dates (e.g. sea ice after mid-2026) and spatial gaps near coasts or under heavy clouds.
* Motion data includes a few anomalous jumps which we have flagged but retained.

## 11. Recommendation for the next preprocessing step
* **Phase 8.2 (Data Splitting & Imputation)**: The dataset should be split chronologically into train/val/test *before* applying any time-series imputation or scaling to prevent data leakage. Missing values should then be interpolated safely within the training envelope.
