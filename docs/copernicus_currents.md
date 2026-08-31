# Copernicus Ocean Currents Data Acquisition

## Selected Product
- **Product ID:** `GLOBAL_MULTIYEAR_PHY_001_030`
- **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
- **Name:** Global Ocean Physics Reanalysis

## Why it was selected
This product is a global ocean physics reanalysis (GLORYS12V1) providing daily data from 1993 onward at a high spatial resolution. It is the gold standard for historical ocean state and provides the necessary current velocities across the entire Antarctic region over our required timeframe (2020-2026). It also contains sea-ice variables which may be useful in later phases.

## Variables
- `uo`: Eastward sea-water velocity (m/s)
- `vo`: Northward sea-water velocity (m/s)

## Resolution
- **Spatial:** 0.083° × 0.083° (approx. 8-9 km at the equator, finer near Antarctica)
- **Temporal:** Daily

## Coverage
- **Temporal Coverage:** 1993-01-01 to present. Our specific bounding subset dynamically uses the minimum and maximum timestamps of the actual iceberg trajectory dataset (plus a 1-day margin).
- **Spatial Coverage:** Global. Our subset dynamically queries the minimum and maximum latitudes and longitudes from the trajectory dataset (plus a 2.0° margin).

## Subset Strategy
Instead of downloading the entire global NetCDF files spanning years, we extract bounding box parameters directly from `data/processed/iceberg_motion.parquet`. 
This creates a tight spatio-temporal bounding box covering all known iceberg tracks, significantly reducing download sizes, memory constraints, and processing time.

## Credential Handling
Copernicus credentials (`COPERNICUSMARINE_USERNAME` and `COPERNICUSMARINE_PASSWORD`) are strictly managed through environment variables or a local `.env` file (which is ignored by Git). They are never hard-coded in scripts or YAML configuration files.

## Expected Output Format
The subset operation via the `copernicusmarine` Python API will output a targeted NetCDF-4 (`.nc`) file containing only the requested variables (`uo`, `vo`), for the surface depth layer, constrained to our exact bounds.

## Limitations
- **File Size:** Even with tight bounding boxes, the data over several years at 1/12 degree resolution can exceed several gigabytes.
- **Latency:** Extracting multi-year subsets from the Copernicus Marine Service can take time due to their internal processing limits. Batching requests by year or month may be required in the future if API limits or timeouts are hit.
