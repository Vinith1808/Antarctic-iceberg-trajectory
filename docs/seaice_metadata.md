# Phase 7: Sea-Ice Environment Data Acquisition

## 7.1 CMEMS API / Metadata Verification (Live)

Target Product: `GLOBAL_MULTIYEAR_PHY_001_030`
Target Dataset: `cmems_mod_glo_phy_my_0.083deg_P1D-m`

**Live Verification Results:**
1. **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
2. **Product ID:** `GLOBAL_MULTIYEAR_PHY_001_030`
3. **Variable name:** `siconc`
4. **Variable description:** `sea_ice_area_fraction`
5. **Units:** `1` (fraction, 0-1)
6. **Valid range:** 0.0 to 1.0
7. **Fill/missing value:** Standard NetCDF `NaN`
8. **Spatial resolution:** 0.08333° (~8 km)
9. **Temporal resolution:** Daily
10. **Available date range:** `1993-01-01` to `2026-06-23`
11. **Antarctic spatial coverage:** Yes (Latitude -80.0 to 90.0)
12. **Depth/level requirements:** Surface only (`siconc` does not have a depth coordinate)
13. **Coordinate system:** Regular Latitude/Longitude (WGS 84)
14. **Support for 2020-12-31 to 2026-08-16 range:** **NO.** The dataset ends on `2026-06-23`. Observations from July and August 2026 will fall outside the temporal coverage.
15. **Existing credentials:** Yes, existing `.env` credentials provide full access.
16. **Separate licence required:** No, standard CMEMS terms already apply to the account.
17. **Estimated data size:** ~30-50 MB total. By using monthly active-box subsetting without a depth dimension, the chunks will be extremely small (1-2 MB per month).

## 7.2 Trajectory Coverage Analysis
Input: `data/processed/iceberg_motion.parquet`

*   **Total observations:** 2,709
*   **Unique iceberg IDs:** 110
*   **Observation date range:** 2020-12-31 to 2026-08-16
*   **Unique dates:** 162
*   **Unique coordinates:** 1,612
*   **Latitude range:** -77.48 to 0.0
*   **Longitude range:** -179.90 to 179.97

## 7.3 Recommended Extraction Architecture

**Approach: Observation-Driven Active-Month Batching (Same as Phase 6)**
1. Group the 2,709 observations by `year_month` (26 total months).
2. For each active month, calculate the spatial bounding box [min_lat, min_lon, max_lat, max_lon] covering the icebergs, plus a 0.5° margin.
3. Use the `copernicusmarine` Python client to download the spatial/temporal subset for `siconc` (surface only).
4. Perform a `nearest` nearest-neighbor lookup in `xarray` to assign `siconc` to the exact iceberg observation.
5. If the `year_month` is July or August 2026 (beyond the dataset limit of `2026-06-23`), explicitly flag those rows as `OUTSIDE_COVERAGE` rather than crashing.

*Note: Since we are dealing with Sea Ice Concentration, iceberg observations near the equator (e.g. Latitude 0.0) or outside the ice pack will cleanly match `0.0` or `NaN` and be flagged appropriately. No mock data will be used.*
