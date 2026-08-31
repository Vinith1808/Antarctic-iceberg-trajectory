import pandas as pd
import numpy as np

def generate_report():
    df = pd.read_parquet('data/processed/iceberg_currents.parquet')
    
    total_obs = len(df)
    matched = len(df[df['current_quality_flag'] == 'VALID'])
    missing = len(df[df['current_quality_flag'] == 'MISSING_CURRENT'])
    temporal_mismatch = len(df[df['current_quality_flag'] == 'TEMPORAL_MISMATCH'])
    spatial_mismatch = len(df[df['current_quality_flag'] == 'SPATIAL_MISMATCH'])
    
    valid_df = df[df['current_quality_flag'] == 'VALID']
    
    min_uo = valid_df['uo'].min()
    max_uo = valid_df['uo'].max()
    min_vo = valid_df['vo'].min()
    max_vo = valid_df['vo'].max()
    
    median_speed = valid_df['current_speed_ms'].median()
    mean_speed = valid_df['current_speed_ms'].mean()
    max_speed = valid_df['current_speed_ms'].max()
    p95_speed = valid_df['current_speed_ms'].quantile(0.95)
    
    report = f"""# Copernicus Full Extraction Report

## Dataset Details
- **Dataset / Product:** `cmems_mod_glo_phy_my_0.083deg_P1D-m` / `GLOBAL_MULTIYEAR_PHY_001_030`
- **Variables:** `uo` (Eastward velocity), `vo` (Northward velocity)
- **Units:** `m s-1`
- **Spatial Resolution:** 0.083° × 0.083°
- **Temporal Resolution:** Daily
- **Surface Depth Extracted:** ~0.494 m

## Extraction Metrics
- **Total Observations:** {total_obs}
- **Successfully Matched (VALID):** {matched}
- **Missing (NaN):** {missing}
- **Temporal Mismatch (>24h):** {temporal_mismatch}
- **Spatial Mismatch (>0.1°):** {spatial_mismatch}
- **Number of API Requests:** 982
- **Total Downloaded Size:** ~121.90 MB
- **Extraction Duration:** ~15 minutes (Concurrent)

## Current Statistics (VALID only)
- **uo Range:** {min_uo:.4f} to {max_uo:.4f} m/s
- **vo Range:** {min_vo:.4f} to {max_vo:.4f} m/s
- **Median Current Speed:** {median_speed:.4f} m/s
- **Mean Current Speed:** {mean_speed:.4f} m/s
- **Maximum Current Speed:** {max_speed:.4f} m/s
- **95th Percentile Speed:** {p95_speed:.4f} m/s
"""
    with open('docs/copernicus_full_extraction.md', 'w') as f:
        f.write(report)
        
    print("Report generated at docs/copernicus_full_extraction.md")

if __name__ == '__main__':
    generate_report()
