# Phase 8.2: Missing Data & Data Quality Analysis

## 1. General Statistics
* **Observations:** 2709
* **Unique Icebergs:** 110
* **Duplicates:** 0
* **Observations per Iceberg:** Min: 1, Median: 25.5, Max: 61

## 2. Temporal Gaps (`time_since_previous_observation_hours`)
* **Min:** 24.00 hours
* **Median:** 192.00 hours
* **Mean:** 707.01 hours
* **75th Percentile:** 288.00 hours
* **95th Percentile:** 768.00 hours
* **Max:** 14160.00 hours

*Note on Sequence Modeling:* The max gap of 14160.00 hours (approx 590.0 days) is an extreme outlier. Standard LSTM models assume uniform time steps. The 95th percentile (768.00h) shows most data is sampled at roughly daily to bi-daily intervals. We will need to either encode `time_since_previous_observation_hours` as an explicit input feature (time-aware LSTM/Transformer) or resample trajectories.

## 3. Velocity Distribution
* **Min:** 0.0000 m/s
* **Median:** 0.0045 m/s
* **Mean:** 0.0326 m/s
* **Max:** 4.0114 m/s

## 4. Missing Environmental Data
- **uo**: 491 missing (18.12%)
- **vo**: 491 missing (18.12%)
- **current_speed_ms**: 491 missing (18.12%)
- **current_direction_deg**: 491 missing (18.12%)
- **u10**: 0 missing (0.00%)
- **v10**: 0 missing (0.00%)
- **wind_speed_ms**: 0 missing (0.00%)
- **wind_direction_deg**: 0 missing (0.00%)
- **siconc**: 930 missing (34.33%)


### Missingness Causes (via Quality Flags)
**Ocean Currents:**
current_quality_flag
VALID                2183
OUTSIDE_COVERAGE      261
MISSING_CURRENT       228
TEMPORAL_MISMATCH      35

**Wind (ERA5):**
wind_quality_flag
VALID    2709

**Sea Ice (CMEMS):**
seaice_quality_flag
VALID               1779
MISSING_SIC          631
OUTSIDE_COVERAGE     299

*Analysis:* 
- Missingness in Sea Ice is predominantly caused by `OUTSIDE_COVERAGE` (dates > 2026-06-23).
- Missingness in currents/wind is largely due to spatial coverage/landmask proximity or minor API failures.

## 5. Interpolation Strategy Recommendation
**Recommendation: E. Retain NaN and use availability masks.**

*Reasoning:* 
1. The environmental parameters (wind, current, ice) change rapidly. Forward filling or interpolating over large temporal gaps (e.g., >48 hours) will introduce massive physical inaccuracies (e.g. hallucinating a storm that has passed).
2. We cannot safely interpolate sea ice for dates beyond `2026-06-23` (OUTSIDE_COVERAGE), as this would project past dataset validity.
3. Neural networks (especially transformers or masked LSTMs) can natively handle missing values if provided with the availability indicators (`current_available`, `wind_available`, `seaice_available`) which we have already created.
4. We can use 0 for missing values *only after splitting*, as long as the availability mask is explicitly provided to the model.

If we *must* interpolate for a standard LSTM, we recommend **D. Limited interpolation (max gap = 24 hours)** followed by masking. For now, we will leave them as NaN in the split files to prevent silent leakage.
