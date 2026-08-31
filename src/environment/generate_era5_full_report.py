import pandas as pd
import numpy as np
from pathlib import Path
import time

def generate_full_report():
    in_path = Path('data/processed/iceberg_wind.parquet')
    out_path = Path('docs/era5_full_extraction.md')
    
    if not in_path.exists():
        print(f"File {in_path} not found.")
        return
        
    start_time = time.time()
    df = pd.read_parquet(in_path)
    
    total = len(df)
    unique_icebergs = df['iceberg_id'].nunique()
    
    df['year_month'] = df['timestamp'].dt.to_period('M')
    monthly_requests = df['year_month'].nunique()
    
    valid = len(df[df['wind_quality_flag'] == 'VALID'])
    missing = len(df[df['wind_quality_flag'] == 'MISSING_WIND'])
    temporal = len(df[df['wind_quality_flag'] == 'TEMPORAL_MISMATCH'])
    spatial = len(df[df['wind_quality_flag'] == 'SPATIAL_MISMATCH'])
    outside = len(df[df['wind_quality_flag'] == 'OUTSIDE_COVERAGE'])
    
    valid_df = df[df['wind_quality_flag'] == 'VALID']
    missing_u10 = df['u10'].isna().sum()
    missing_v10 = df['v10'].isna().sum()
    
    # Calculate downloaded size roughly from nc files
    nc_dir = Path('data/raw/environment/era5')
    total_size_mb = 0
    if nc_dir.exists():
        total_size_mb = sum(f.stat().st_size for f in nc_dir.glob('*.nc')) / (1024*1024)
        
    successful_requests = len(list(nc_dir.glob('*.nc'))) if nc_dir.exists() else 0
    failed_requests = monthly_requests - successful_requests
        
    with open(out_path, 'w') as f:
        f.write("# Phase 6.1: Full ERA5 Wind Production Extraction Report\n\n")
        
        f.write("## 1. Extraction Summary\n")
        f.write(f"- **Total Observations processed:** {total}\n")
        f.write(f"- **Unique Icebergs:** {unique_icebergs}\n")
        f.write(f"- **Monthly Requests Initiated:** {monthly_requests}\n")
        f.write(f"- **Successful Requests:** {successful_requests}\n")
        f.write(f"- **Failed Requests:** {failed_requests}\n")
        f.write(f"- **Total Downloaded Data Size:** {total_size_mb:.2f} MB\n\n")
        
        f.write("## 2. Quality Flags (Match Results)\n")
        f.write(f"- `VALID`: {valid}\n")
        f.write(f"- `MISSING_WIND`: {missing}\n")
        f.write(f"- `TEMPORAL_MISMATCH`: {temporal}\n")
        f.write(f"- `SPATIAL_MISMATCH`: {spatial}\n")
        f.write(f"- `OUTSIDE_COVERAGE`: {outside}\n\n")
        
        f.write("## 3. Data Statistics (VALID points only)\n")
        f.write(f"- **Missing u10 values:** {missing_u10}\n")
        f.write(f"- **Missing v10 values:** {missing_v10}\n\n")
        
        if valid > 0:
            f.write("### u10 (Eastward Wind Component, m/s)\n")
            f.write(f"- Min: {valid_df['u10'].min():.4f}\n")
            f.write(f"- Max: {valid_df['u10'].max():.4f}\n")
            f.write(f"- Mean: {valid_df['u10'].mean():.4f}\n")
            f.write(f"- Median: {valid_df['u10'].median():.4f}\n\n")
            
            f.write("### v10 (Northward Wind Component, m/s)\n")
            f.write(f"- Min: {valid_df['v10'].min():.4f}\n")
            f.write(f"- Max: {valid_df['v10'].max():.4f}\n")
            f.write(f"- Mean: {valid_df['v10'].mean():.4f}\n")
            f.write(f"- Median: {valid_df['v10'].median():.4f}\n\n")
            
            f.write("### Wind Speed (m/s)\n")
            f.write(f"- Min: {valid_df['wind_speed_ms'].min():.4f}\n")
            f.write(f"- Max: {valid_df['wind_speed_ms'].max():.4f}\n")
            f.write(f"- Mean: {valid_df['wind_speed_ms'].mean():.4f}\n")
            f.write(f"- Median: {valid_df['wind_speed_ms'].median():.4f}\n\n")
            
            f.write("### Wind Direction (deg)\n")
            f.write(f"- Min: {valid_df['wind_direction_deg'].min():.1f}\n")
            f.write(f"- Max: {valid_df['wind_direction_deg'].max():.1f}\n")
            f.write(f"- Mean: {valid_df['wind_direction_deg'].mean():.1f}\n")
            f.write(f"- Median: {valid_df['wind_direction_deg'].median():.1f}\n")
            
    print(f"Report generated successfully at {out_path}")

if __name__ == '__main__':
    generate_full_report()
