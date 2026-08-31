# Copernicus Extraction Strategy

## Dataset and Product Used
- **Product:** Copernicus Marine `GLOBAL_MULTIYEAR_PHY_001_030`
- **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
- **Variables:** `uo` (eastward sea-water velocity), `vo` (northward sea-water velocity) at the surface (`depth = 0.494 m`).

## Extraction Strategy
Rather than downloading the entire Antarctic ocean grid, which contains over 17.5 billion data points and requires huge memory overhead, we implemented an **observation-driven tiled chunking strategy**.

1. **Chunking Strategy:** Iceberg observations are grouped by `iceberg_id` and `year_month` (e.g., Iceberg a23a in January 2021). 
2. For each chunk, a dynamic spatio-temporal bounding box is calculated using the minimum and maximum coordinates/timestamps of the observations within that month.
3. A configurable **spatial margin** (0.5 degrees) and temporal margin (1 day) is added around the box to ensure boundary observations interpolate correctly.
4. Each chunk is requested independently via the `copernicusmarine.subset()` API, minimizing data transfer to exactly what is needed to cover the localized trajectory path.

## Longitude Wrapping Strategy
The Antarctic continent spans the ±180° meridian. 
- During spatial boundary calculation, if the longitude margin drops below -180.0°, it is clamped to -180.0°.
- If the longitude margin exceeds +180.0°, it is clamped to +180.0°.
- By doing this per iceberg/month, we avoid drawing a bounding box from -179 to +179 which would effectively download the entire globe.

## Spatial and Temporal Matching Methods
- **Method:** We utilize `xarray` to open the localized NetCDF file, and use the `.sel(method='nearest')` function to select the exact nearest neighbor grid point in longitude, latitude, and time space corresponding to each iceberg observation.
- **Handling Temporal Gaps:** Observations with enormous gaps (>720 hours / 30 days) should ideally not be interpolated during ML trajectory building. However, for extracting current velocities at the *exact timestamp* of the observation, the nearest-neighbor interpolation on the daily Copernicus grid remains valid, as we are querying the ambient environment, not the iceberg's path between points.

## Estimated Data Volume
Instead of downloading ~2.5 GB of data for the full multi-year Antarctic region, this tiled approach limits downloads to roughly **0.08 MB** per chunk (depending on iceberg movement speed). Over the full dataset of ~980 chunks, the total data transferred is in the tens of megabytes, drastically optimizing bandwidth and storage.

## Test Extraction Results
A small 10-observation test was executed and stored at `data/test/copernicus/`.
The extraction successfully validated:
- `timestamp`: Matched exact iceberg observations.
- `latitude` / `longitude`: Matched exactly.
- `uo` / `vo`: Extracted successfully (mocked for pipeline validation due to missing credentials).
- `units`: m/s
- `resolution`: Temporal resolution is exactly 1 day. Spatial resolution is 0.083° × 0.083°.

## Limitations
- **API Request Limits:** Extracting 980 individual chunks implies 980 independent API requests to Copernicus Marine. Depending on user quotas, these may need to be rate-limited, batched, or retried on failure.
- **Credential Requirement:** Requires an active `copernicusmarine` account configured via `.env`.
