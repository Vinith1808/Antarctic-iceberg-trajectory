# Copernicus Real Extraction Test

This document validates the observation-driven chunk extraction architecture directly against the Copernicus Marine production API.

## 1. Dataset Verification
- **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
- **Product / Source ID:** `GLOBAL_MULTIYEAR_PHY_001_030` (MERCATOR GLORYS12V1)
- **Time Range Available:** 1993-01-01 to near-present
- **Temporal Resolution:** Daily
- **Spatial Resolution:** 0.083° × 0.083° (approx 8km)
- **Coordinates:** `depth`, `latitude`, `longitude`, `time`
- **Depth Extracted:** `0.494 m` (Surface / Nearest valid surface layer)

## 2. Variables & Units
- **`uo`**: Eastward velocity (`m s-1`)
- **`vo`**: Northward velocity (`m s-1`)

## 3. Test Details
- **Observations Requested:** 10
- **Observations Successfully Matched:** 10
- **Missing Values (NaNs):** 0
- **Total API Requests/Chunks:** 3
- **Extraction Time:** ~30 seconds (approx. 10s per chunk)
- **Output File Size (NetCDF + CSV):** ~85 KB total

## 4. Returned Values
The following table shows the real extracted values from the API (not the `0.1` / `0.05` mock values). 
The `uo` and `vo` velocities are successfully localized nearest-neighbor matches of the sea-water current at the exact iceberg timestamp and coordinate.

| iceberg_id | timestamp | latitude | longitude | uo (m/s) | vo (m/s) |
|---|---|---|---|---|---|
| a23a | 2021-01-17 | -75.816667 | -40.550000 | -0.017701 | 0.009766 |
| a23a | 2021-01-23 | -75.800000 | -40.200000 | -0.090945 | 0.050050 |
| a23a | 2021-02-01 | -75.750000 | -40.000000 | -0.003662 | 0.042726 |
| a23a | 2021-02-06 | -75.750000 | -40.000000 | -0.004883 | 0.045778 |
| a23a | 2021-02-09 | -75.750000 | -40.000000 | -0.003052 | 0.062868 |
| a23a | 2021-02-20 | -75.750000 | -40.000000 | -0.091556 | -0.060427 |
| a23a | 2021-03-01 | -75.750000 | -40.000000 | -0.081790 | -0.034181 |
| a23a | 2021-03-10 | -75.716667 | -39.983333 | -0.104984 | -0.068972 |
| a23a | 2021-03-13 | -75.716667 | -39.983333 | -0.097049 | -0.004883 |
| a23a | 2021-03-31 | -75.683333 | -39.833333 | -0.002441 | 0.048219 |

## 5. Summary
The real API connection confirms:
- **Authentication:** Operational via environment variables without hardcoding.
- **Mock Safety Check:** Successfully disabled. Real values are explicitly returned.
- **Target Resolution:** Coordinates are within actual dataset coverage.
- **Interpolation:** Nearest neighbor correctly matched bounding constraints without throwing out-of-bounds exceptions or yielding unexpected null values.
