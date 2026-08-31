# ERA5 Metadata (Phase 6)

* **Dataset Identifier:** `reanalysis-era5-single-levels`
* **Variables:** 
  * `10m_u_component_of_wind` (u10)
  * `10m_v_component_of_wind` (v10)
* **Units:** `m s-1`
* **Temporal Resolution:** Hourly
* **Spatial Resolution:** 0.25° × 0.25° (~27 km at equator)
* **Available Time Range:** 1940 to present (updated continuously with ~5 days latency)
* **Longitude Convention:** Typically [-180, 180] when sliced using the `area` parameter (`[North, West, South, East]`).
* **Latitude Ordering:** Decreasing (North to South).
* **Data Format:** NetCDF (`format: 'netcdf'`)
* **Official API/Access Method:** Climate Data Store (CDS) API via `cdsapi` Python client.
* **Current Availability:** Available up to the last ~5 days, completely covering our 2020 to mid-2026 dataset.

## Temporal Matching
* **Strategy:** Match iceberg observation timestamp to the **nearest hour**.
* **Tolerance:** Maximum acceptable mismatch is ±30 minutes. Observations outside this tolerance are flagged as `TEMPORAL_MISMATCH`. Interpolation is not used.

## Spatial/Temporal Batching
* **Strategy:** Observations are grouped by active `year_month`. For each month, a single dynamic spatial bounding box (`[North, West, South, East]`) is calculated covering all active icebergs in that month plus a configurable spatial margin (e.g., 0.5°).
* **Benefit:** Reduces API requests dramatically (e.g., from 982 individual iceberg-level chunks to <100 active month chunks), preventing the script from stalling in the CDS API queue while remaining highly spatially efficient.
