# Dataset Inspection Report: Zenodo Iceberg Vector Outline

## Overview
This report details the exploratory inspection of the Zenodo iceberg vector dataset located in `data/raw/iceberg/Iceberg vector outline/`. The inspection was performed using Geopandas to ensure data integrity without modifying the raw files.

## 1. Directory Structure
```text
data/raw/iceberg/Iceberg vector outline/
├── 201810_distribution.gpkg
├── 201910_distribution.gpkg
├── 202010_distribution.gpkg
├── 202110_distribution.gpkg
├── 202210_distribution.gpkg
└── 202310_distribution.gpkg
```

## 2. File Overview
- **File Format:** GeoPackage (`.gpkg`)
- **Temporal Resolution:** Annual snapshots (specifically October of each year).
- **Coordinate Reference System (CRS):** EPSG:3031 (WGS 84 / Antarctic Polar Stereographic)
- **Geometry Types:** `MultiPolygon`, `Polygon`, `GeometryCollection`

## 3. Dataset Volume & Records
| Filename | Size (MB) | Number of Records |
|----------|-----------|-------------------|
| `201810_distribution.gpkg` | 110.06 | 34,825 |
| `201910_distribution.gpkg` | 160.76 | 39,261 |
| `202010_distribution.gpkg` | 162.37 | 38,066 |
| `202110_distribution.gpkg` | 46.86 | 51,420 |
| `202210_distribution.gpkg` | 34.88 | 36,186 |
| `202310_distribution.gpkg` | 43.52 | 44,537 |
| **Total** | **~558.45** | **244,295** |

## 4. Attributes & Schema
The dataset contains 10 exact attributes:

| Column | Data Type | Description |
|--------|-----------|-------------|
| `lon` | `float64` | Longitude coordinate |
| `lat` | `float64` | Latitude coordinate |
| `area_km2` | `float64` | Area of the iceberg (km²) |
| `area_uncertainty_km2`| `float64` | Uncertainty in area measurement (km²) |
| `perimeter_km` | `float64` | Perimeter of the iceberg (km) |
| `long_axis_km` | `float64` | Long axis length (km) |
| `short_axis_km` | `float64` | Short axis length (km) |
| `mass_gt` | `float64` | Mass of the iceberg (Gigatonnes) |
| `mass_uncertainty_gt`| `float64` | Uncertainty in mass measurement (Gt) |
| `geometry` | `geometry` | Vector geometry object |

## 5. Summary of Findings
- **Missing Values:** `0` missing values across all columns and files.
- **Latitude Range:** `[-79.9445, -55.0595]`
- **Longitude Range:** `[-179.9796, 179.9623]`
- **Date/Year Info:** Only inferred from the filename (e.g., `201810` = October 2018). There is no explicit temporal field in the tabular data.
- **Iceberg Identifiers:** **None**. There is no unique ID tracking icebergs.
- **Continuous Trajectories vs. Snapshots:** The dataset consists of **annual snapshots** rather than continuous trajectories. Without an ID field, tracking the exact same iceberg across years is not directly possible natively without spatial-matching heuristics.

## Recommended Next Step
Because this dataset only contains annual snapshots without iceberg tracking IDs, it cannot be used natively to train an auto-regressive trajectory model (which requires timeseries data of the same icebergs over time). 
The next step is to obtain continuous iceberg tracking data (e.g., BYU / Brigham Young University Antarctic Iceberg tracking database or similar continuous trajectory products).
