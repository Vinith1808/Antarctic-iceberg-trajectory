# Dataset Inspection Report: NASA SCP Iceberg Tracking (Joel-Hanson)

## Overview
This report details the inspection of the NASA SCP Iceberg Tracking dataset (`iceberg_location.json`). The dataset provides time-series tracking data of Antarctic icebergs.

## 1. JSON Structure
The JSON is structured as a dictionary. 
- **Keys:** Observation dates (e.g., `"02/12/21"`).
- **Values:** Arrays of JSON objects, where each object represents an iceberg's location on or near that date.

## 2. General Statistics
- **Total Observations:** 2,939
- **Unique Iceberg IDs:** 110
- **Observation Date Range:** 2020-12-31 to 2026-08-16

## 3. Exact Fields / Schema
| Field Name | Type | Description |
|------------|------|-------------|
| `iceberg` | String | The exact iceberg identifier (e.g., `"a23a"`). |
| `recent_observation` | String | The exact observation date of the iceberg (`MM/DD/YY`). |
| `lattitude` | Float | The numerical representation of latitude (NOTE: misspelled in raw data). |
| `longitude` | Float | The numerical representation of longitude. |
| `dms_lattitude` | String | Latitude in Degrees, Minutes, Seconds format (e.g., `"75 45'S"`). |
| `dms_longitude` | String | Longitude in Degrees, Minutes, Seconds format (e.g., `"40 0'W"`). |

## 4. Continuity & Tracking
- **Observations per Iceberg:** 
  - Mean: ~26.7
  - Median: 26.0
  - Max: 64
  - Min: 1
- **Time Interval Between Observations:**
  - Mean interval: ~27 days
  - Median interval: 8 days
- **ID Persistence:** Yes, iceberg IDs persist across multiple observations.
- **Suitability for Sequence Modeling:** **Highly Suitable**. With a median of 26 observations per iceberg and regular temporal intervals (typically 1-2 weeks), many icebergs have sufficient trajectory sequences to train auto-regressive or RNN/LSTM-based models.

## 5. Data Quality & Anomalies
- **Missing Values:** `0` missing values in the raw dataset.
- **Duplicate Observations:** There are `230` duplicated records (same iceberg, same date) resulting from the snapshot-key structure overlapping with the `recent_observation` date.
- **Invalid Coordinates Formatting:** The numeric `lattitude` and `longitude` fields are **not** in standard decimal degrees. 
  - `lattitude` range: `[-7729.0, 0.0]`
  - `longitude` range: `[-17954.0, 17958.0]`
  - **Reason:** The float values encode degrees and minutes directly without decimal conversion (e.g., `"75 45'S"` becomes `-7545.0` instead of `-75.75`). *This must be corrected during the data preprocessing phase.*
- **Geographic Coverage:** Approximate range spans the entire Antarctic coast (Latitudes up to ~-77°S).

## 6. Recommended Next Step
This dataset provides the essential trajectory continuity missing from the Zenodo dataset. 
The recommended next step is to create a preprocessing pipeline that:
1. Flattens the JSON into a tabular format.
2. Removes duplicate iceberg-date records.
3. Converts the non-standard numeric `lattitude`/`longitude` values (or the string `dms_lattitude`/`dms_longitude`) into standard decimal degrees (WGS84).
4. Interpolates missing days to create uniformly sampled time-series tracks.
