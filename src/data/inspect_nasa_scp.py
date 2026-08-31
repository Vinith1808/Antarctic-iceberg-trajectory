import os
import json
import pandas as pd
from pathlib import Path

def inspect_nasa_dataset():
    file_path = Path('data/raw/iceberg/nasa_scp/iceberg_location.json')
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    print(f"JSON Structure: Dictionary with {len(data)} keys (dates), containing lists of objects.")
    
    # Flatten JSON
    records = []
    for dict_date, icebergs in data.items():
        for ibg in icebergs:
            record = ibg.copy()
            record['dict_date'] = dict_date
            records.append(record)
            
    df = pd.DataFrame(records)
    
    print(f"Total Observations: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    unique_ids = df['iceberg'].nunique()
    print(f"Unique Iceberg IDs: {unique_ids}")
    
    # Dates
    df['recent_observation'] = pd.to_datetime(df['recent_observation'], format='%m/%d/%y', errors='coerce')
    df['dict_date'] = pd.to_datetime(df['dict_date'], format='%m/%d/%y', errors='coerce')
    
    min_date = df['recent_observation'].min()
    max_date = df['recent_observation'].max()
    print(f"Observation Date Range: {min_date.date()} to {max_date.date()}")
    
    # Observations per iceberg
    obs_counts = df['iceberg'].value_counts()
    print("Observations per iceberg (Summary):")
    print(obs_counts.describe())
    
    # Sort and calculate time intervals
    df = df.sort_values(by=['iceberg', 'recent_observation'])
    df['time_diff'] = df.groupby('iceberg')['recent_observation'].diff().dt.days
    print("Time interval between observations (days):")
    print(df['time_diff'].describe())
    
    # Duplicates
    duplicates = df.duplicated(subset=['iceberg', 'recent_observation']).sum()
    print(f"Duplicate observations (same iceberg, same date): {duplicates}")
    
    # Missing values
    print("Missing Values:")
    print(df.isna().sum())
    
    # Coordinate range (raw values)
    print(f"Raw Latitude ('lattitude') Range: [{df['lattitude'].min()}, {df['lattitude'].max()}]")
    print(f"Raw Longitude ('longitude') Range: [{df['longitude'].min()}, {df['longitude'].max()}]")
    
    # Valid coordinates?
    valid_lat = df['lattitude'].between(-90, 90).all()
    valid_lon = df['longitude'].between(-180, 180).all()
    print(f"Are all raw latitudes between -90 and 90? {valid_lat}")
    print(f"Are all raw longitudes between -180 and 180? {valid_lon}")

if __name__ == '__main__':
    inspect_nasa_dataset()
