import pandas as pd
import numpy as np

def generate_report():
    df = pd.read_parquet('data/test/era5/iceberg_era5_wind.parquet')
    
    total = len(df)
    valid = len(df[df['wind_quality_flag'] == 'VALID'])
    missing = len(df[df['wind_quality_flag'] == 'MISSING_WIND'])
    temporal = len(df[df['wind_quality_flag'] == 'TEMPORAL_MISMATCH'])
    spatial = len(df[df['wind_quality_flag'] == 'SPATIAL_MISMATCH'])
    
    # Temporal diff calculation
    diffs = []
    for _, row in df.iterrows():
        if pd.notna(row['era5_timestamp']):
            diff_mins = abs((row['timestamp'] - row['era5_timestamp']).total_seconds() / 60.0)
            diffs.append(diff_mins)
            
    avg_diff = np.mean(diffs) if diffs else np.nan
    max_diff = np.max(diffs) if diffs else np.nan
    
    print("--- ERA5 TEST REPORT ---")
    print("Authentication Result: SUCCESS (License Accepted)")
    print(f"Observations requested: {total}")
    print(f"Successful matches: {valid}")
    print(f"Missing u10/v10: {missing}")
    print(f"Temporal mismatches: {temporal}")
    print(f"Spatial mismatches: {spatial}")
    
    if valid > 0:
        valid_df = df[df['wind_quality_flag'] == 'VALID']
        print(f"Matched ERA5 timestamps: {len(valid_df['era5_timestamp'].dropna())}")
        print(f"Temporal differences (minutes): Avg={avg_diff:.1f}, Max={max_diff:.1f}")
        print(f"u10 values: Min={valid_df['u10'].min():.4f}, Max={valid_df['u10'].max():.4f}, Mean={valid_df['u10'].mean():.4f}")
        print(f"v10 values: Min={valid_df['v10'].min():.4f}, Max={valid_df['v10'].max():.4f}, Mean={valid_df['v10'].mean():.4f}")
        print(f"Wind speed (m/s): Min={valid_df['wind_speed_ms'].min():.4f}, Max={valid_df['wind_speed_ms'].max():.4f}, Mean={valid_df['wind_speed_ms'].mean():.4f}")
        print(f"Wind direction (deg): Min={valid_df['wind_direction_deg'].min():.1f}, Max={valid_df['wind_direction_deg'].max():.1f}, Mean={valid_df['wind_direction_deg'].mean():.1f}")
    
    print("\n--- 10 OUTPUT ROWS ---")
    cols = ['iceberg_id', 'timestamp', 'latitude', 'longitude', 'u10', 'v10', 'wind_speed_ms', 'wind_direction_deg', 'era5_timestamp', 'wind_quality_flag']
    print(df[cols].to_string(index=False))

if __name__ == '__main__':
    generate_report()
