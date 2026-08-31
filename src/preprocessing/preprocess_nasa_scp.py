import pandas as pd
import json
from pathlib import Path
import re
import numpy as np
import sys

def convert_dms(dms_str):
    """
    Converts string like "75 45'S" or "0'N" to decimal degrees.
    """
    if pd.isna(dms_str):
        return np.nan
    
    dms_str = str(dms_str).strip()
    match = re.match(r'^(?:(\d+)\s+)?(\d+)\'([NSEW])$', dms_str)
    
    if match:
        d_str = match.group(1)
        m_str = match.group(2)
        dir_char = match.group(3)
        
        d = float(d_str) if d_str else 0.0
        m = float(m_str)
        
        val = d + (m / 60.0)
        
        if dir_char in ['S', 'W']:
            val = -val
            
        return val
        
    return np.nan

def process_nasa_dataset():
    raw_path = Path('data/raw/iceberg/nasa_scp/iceberg_location.json')
    out_parquet = Path('data/processed/iceberg_tracks.parquet')
    out_csv = Path('data/processed/iceberg_track_summary.csv')
    
    if not raw_path.exists():
        print(f"Error: {raw_path} not found.")
        sys.exit(1)
        
    print("1. Loading raw JSON...")
    with open(raw_path, 'r') as f:
        data = json.load(f)
        
    print("2. Flattening dictionary into tabular format...")
    records = []
    for dict_date, icebergs in data.items():
        for ibg in icebergs:
            records.append(ibg)
            
    df = pd.DataFrame(records)
    obs_before = len(df)
    
    print("3. Renaming columns...")
    df = df.rename(columns={
        'iceberg': 'iceberg_id',
        'recent_observation': 'timestamp',
        'lattitude': 'raw_latitude',
        'longitude': 'raw_longitude'
    })
    
    print("5. Parsing timestamp...")
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y', errors='coerce')
    
    print("6. Converting coordinates using DMS fields...")
    df['latitude'] = df['dms_lattitude'].apply(convert_dms)
    df['longitude'] = df['dms_longitude'].apply(convert_dms)
    df['coordinate_conversion_status'] = 'Converted from DMS'
    
    # Mark failures
    failed_mask = df['latitude'].isna() | df['longitude'].isna()
    df.loc[failed_mask, 'coordinate_conversion_status'] = 'Failed'
    
    print("7. Detecting anomalies...")
    invalid_lat = df[~df['latitude'].between(-90, 90)]
    invalid_lon = df[~df['longitude'].between(-180, 180)]
    suspicious_zero_lat = df[df['latitude'] == 0.0]
    suspicious_zero_lon = df[df['longitude'] == 0.0]
    malformed_time = df[df['timestamp'].isna()]
    
    print(f"  - Invalid latitude (< -90 or > 90): {len(invalid_lat)}")
    print(f"  - Invalid longitude (< -180 or > 180): {len(invalid_lon)}")
    print(f"  - Suspicious latitude (== 0): {len(suspicious_zero_lat)}")
    print(f"  - Suspicious longitude (== 0): {len(suspicious_zero_lon)}")
    print(f"  - Malformed timestamps: {len(malformed_time)}")
    
    # 8. Handling duplicates
    exact_duplicates = df.duplicated(subset=['iceberg_id', 'timestamp']).sum()
    print(f"8. Duplicate observations detected: {exact_duplicates}")
    df = df.drop_duplicates(subset=['iceberg_id', 'timestamp']).copy()
    obs_after = len(df)
    print(f"  - Observations after cleaning: {obs_after}")
    
    # 15. Validation Assertions
    print("Validating cleaned dataset...")
    if not df['latitude'].between(-90, 90).all():
        print("ASSERTION FAILED: Latitude out of bounds.")
        print(invalid_lat.head())
        sys.exit(1)
    if not df['longitude'].between(-180, 180).all():
        print("ASSERTION FAILED: Longitude out of bounds.")
        print(invalid_lon.head())
        sys.exit(1)
    if not df['timestamp'].notna().all():
        print("ASSERTION FAILED: Malformed timestamps exist.")
        print(malformed_time.head())
        sys.exit(1)
    if not df['iceberg_id'].notna().all():
        print("ASSERTION FAILED: Null iceberg_id found.")
        sys.exit(1)
    
    print("9. Sorting data chronologically...")
    df = df.sort_values(by=['iceberg_id', 'timestamp']).reset_index(drop=True)
    
    print("10. Calculating temporal metrics...")
    df['observation_index'] = df.groupby('iceberg_id').cumcount()
    df['time_since_previous_observation_hours'] = df.groupby('iceberg_id')['timestamp'].diff().dt.total_seconds() / 3600.0
    
    print("11. Generating trajectory statistics...")
    obs_per_iceberg = df.groupby('iceberg_id').size()
    time_gaps = df['time_since_previous_observation_hours'].dropna()
    
    print(f"  - Number of unique icebergs: {len(obs_per_iceberg)}")
    print(f"  - Observations before cleaning: {obs_before}")
    print(f"  - Exact duplicates removed: {exact_duplicates}")
    print(f"  - Observations after cleaning: {obs_after}")
    print(f"  - Observations per iceberg (Min/Median/Mean/Max): {obs_per_iceberg.min()} / {obs_per_iceberg.median()} / {obs_per_iceberg.mean():.2f} / {obs_per_iceberg.max()}")
    if not time_gaps.empty:
        print(f"  - Temporal gap hours (Min/Median/Max): {time_gaps.min()} / {time_gaps.median()} / {time_gaps.max()}")
    else:
        print("  - Temporal gap hours: N/A")
        
    print(f"  - Icebergs with >= 5 obs: {(obs_per_iceberg >= 5).sum()}")
    print(f"  - Icebergs with >= 10 obs: {(obs_per_iceberg >= 10).sum()}")
    print(f"  - Icebergs with >= 20 obs: {(obs_per_iceberg >= 20).sum()}")
    print(f"  - Icebergs with >= 30 obs: {(obs_per_iceberg >= 30).sum()}")
    print(f"  - Lat Range after cleaning: [{df['latitude'].min():.4f}, {df['latitude'].max():.4f}]")
    print(f"  - Lon Range after cleaning: [{df['longitude'].min():.4f}, {df['longitude'].max():.4f}]")
    print(f"  - Invalid coordinates count: 0 (filtered/asserted)")
    print(f"  - Suspicious coordinates count (Lat/Lon == 0): {len(suspicious_zero_lat) + len(suspicious_zero_lon)}")
    
    print("12. Saving Parquet file...")
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    cols_to_save = [
        'iceberg_id', 'timestamp', 'latitude', 'longitude', 
        'observation_index', 'time_since_previous_observation_hours', 
        'raw_latitude', 'raw_longitude', 'dms_lattitude', 'dms_longitude', 
        'coordinate_conversion_status'
    ]
    df[cols_to_save].to_parquet(out_parquet, index=False)
    
    print("13. Creating CSV summary...")
    summary = df.groupby('iceberg_id').agg(
        observation_count=('observation_index', 'size'),
        first_observation=('timestamp', 'min'),
        last_observation=('timestamp', 'max'),
        median_gap_hours=('time_since_previous_observation_hours', 'median'),
        latitude_min=('latitude', 'min'),
        latitude_max=('latitude', 'max'),
        longitude_min=('longitude', 'min'),
        longitude_max=('longitude', 'max')
    ).reset_index()
    summary.to_csv(out_csv, index=False)
    print("Processing complete.")

if __name__ == '__main__':
    process_nasa_dataset()
