# NASA SCP Dataset Preprocessing

## 1. Original Schema & Initial State
- **Input File:** `data/raw/iceberg/nasa_scp/iceberg_location.json`
- **Structure:** Dictionary where keys are observation dates, and values are arrays of iceberg tracking JSON objects.
- **Initial Observations:** 2,939 records.
- **Initial Schema:** `iceberg`, `recent_observation`, `lattitude`, `longitude`, `dms_lattitude`, `dms_longitude`

## 2. Flattening Procedure
The date-keyed dictionary was flattened into a tabular pandas DataFrame. The outer dictionary key was originally used as a reference date, but the actual tracking date of the iceberg (`recent_observation`) was extracted to serve as the timestamp for trajectory sequences. The dataset was then sorted by `iceberg_id` and `timestamp`.

## 3. Coordinate Encoding Discovered
The original numerical coordinates (`lattitude` and `longitude`) were heavily malformed due to an encoding bug in the source dataset. Instead of decimal degrees, the source data had simply removed the spaces from the DMS (Degrees, Minutes, Seconds) representation.
* Example: `54 47'W` was encoded numerically as `-5447.0` (which implies `-54` degrees and `-47` minutes concatenated, losing the standard geographic meaning). 
* Example: `34 6'W` was encoded numerically as `-346.0`. 
Due to this formatting issue, dividing by 100 or 10 was inconsistent and lossy (e.g. both `34 6'` and `3 46'` could yield `346.0`).

## 4. Coordinate Conversion Method
To correct this, we ignored the numerical `lattitude`/`longitude` fields and parsed the raw `dms_lattitude` and `dms_longitude` strings directly.
**Conversion Rule:**
- Match format: `(?:(\d+)\s+)?(\d+)'([NSEW])`
- Extract degrees ($d$) and minutes ($m$). If degrees were omitted (e.g., `0'N`), $d = 0$.
- Calculate Decimal Degrees: $DD = d + \frac{m}{60.0}$
- If direction is South (`S`) or West (`W`), multiply by `-1`.

## 5. Handling Anomalies
- **Duplicates:** Exact duplicate records (identical `iceberg_id` and `timestamp`) were created due to snapshot overlapping. **230** duplicate records were removed.
- **Invalid Records:** Assertions ensured `latitude` was in `[-90, 90]` and `longitude` in `[-180, 180]`. 0 invalid records were found after correct DMS conversion.
- **Suspicious Records:** 4 records (where either Lat or Lon resolved to strictly `0.0`) were flagged as suspicious (e.g., `0'N`, `0'E`) but retained in the output for auditing purposes.

## 6. Final Dataset Statistics
- **Total Observations After Cleaning:** 2,709
- **Unique Icebergs:** 110
- **Observations per Iceberg:** Median 25.5, Max 61
- **Temporal Gap:** Median interval of 192.0 hours (8 days).
- **Coordinate Range:**
  - Latitude: `[-77.4833, 0.0]`
  - Longitude: `[-179.9, 179.9667]`

## 7. Limitations
- **0.0 Coordinates:** Some coordinates resolved to exact zeroes in the raw DMS strings (e.g., `0'N`, `0'E`). These may indicate missing transmission or bad tracking data for that specific observation.
- **Timestamp Resolution:** Timestamps only contain dates (YYYY-MM-DD), not hours/minutes. Thus, time gaps have a minimum resolution of 24 hours. Velocity calculations over short time periods will have high uncertainty.
