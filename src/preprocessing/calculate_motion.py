import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import sys

# Constants
# Icebergs rarely move faster than 1-2 m/s. 3.0 m/s (10.8 km/h) is extremely fast.
ANOMALOUS_VELOCITY_THRESHOLD_MS = 3.0

def calculate_heading(dx, dy):
    """
    Calculate heading in degrees (0=North, 90=East, 180=South, 270=West).
    In EPSG:3031, Y points North (along 0 deg meridian), X points East (along 90E meridian).
    arctan2(dx, dy) yields 0 when dx=0, dy>0 (North).
    """
    # handle 0 displacement
    if dx == 0 and dy == 0:
        return np.nan
    heading = np.degrees(np.arctan2(dx, dy))
    return heading % 360

def process_motion():
    in_path = Path('data/processed/iceberg_tracks.parquet')
    out_parquet = Path('data/processed/iceberg_motion.parquet')
    out_csv = Path('data/processed/iceberg_motion_summary.csv')
    
    if not in_path.exists():
        print(f"Error: {in_path} not found.")
        sys.exit(1)
        
    df = pd.read_parquet(in_path)
    
    # STEP 1: Coordinate projection (WGS84 -> EPSG:3031)
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    gdf = gdf.to_crs("EPSG:3031")
    df['x_m'] = gdf.geometry.x
    df['y_m'] = gdf.geometry.y
    
    # Sort just to be sure
    df = df.sort_values(['iceberg_id', 'timestamp']).reset_index(drop=True)
    
    # STEP 2 & 3: Calculate displacement and distance
    # Shift to get previous coordinates
    df['prev_x_m'] = df.groupby('iceberg_id')['x_m'].shift(1)
    df['prev_y_m'] = df.groupby('iceberg_id')['y_m'].shift(1)
    
    df['delta_x_m'] = df['x_m'] - df['prev_x_m']
    df['delta_y_m'] = df['y_m'] - df['prev_y_m']
    
    df['distance_m'] = np.sqrt(df['delta_x_m']**2 + df['delta_y_m']**2)
    
    # For the first observation, set to NaN
    is_first = df['observation_index'] == 0
    df.loc[is_first, ['delta_x_m', 'delta_y_m', 'distance_m']] = np.nan
    
    # STEP 4: Calculate velocity
    time_h = df['time_since_previous_observation_hours']
    # If distance is zero, velocity is 0. If time is valid.
    # If time <= 0 or NaN, we can't calculate velocity.
    valid_time = time_h > 0
    df['velocity_ms'] = np.nan
    df.loc[valid_time & ~is_first, 'velocity_ms'] = df.loc[valid_time & ~is_first, 'distance_m'] / (df.loc[valid_time & ~is_first, 'time_since_previous_observation_hours'] * 3600.0)
    
    # Fix zero-distance explicitly (already handled by math above, but just to be explicitly safe)
    zero_dist = (df['distance_m'] == 0)
    df.loc[zero_dist & valid_time, 'velocity_ms'] = 0.0
    
    df['velocity_kmh'] = df['velocity_ms'] * 3.6
    
    # STEP 5: Calculate heading
    df['heading_deg'] = df.apply(lambda row: calculate_heading(row['delta_x_m'], row['delta_y_m']) if not is_first[row.name] and not np.isnan(row['delta_x_m']) else np.nan, axis=1)
    # Ensure zero distance has NaN heading
    df.loc[zero_dist, 'heading_deg'] = np.nan
    
    # STEP 6: Quality Checks
    df['motion_quality_flag'] = 'OK'
    
    # Order matters for mutually exclusive assignment
    # 1. First observation
    df.loc[is_first, 'motion_quality_flag'] = 'FIRST_OBSERVATION'
    # 2. Invalid time
    invalid_time = (~is_first) & (time_h.isna() | (time_h <= 0))
    df.loc[invalid_time, 'motion_quality_flag'] = 'INVALID_TIME'
    # 3. Anomalous velocity (only if not invalid time)
    anom_vel = (~is_first) & (~invalid_time) & (df['velocity_ms'] > ANOMALOUS_VELOCITY_THRESHOLD_MS)
    df.loc[anom_vel, 'motion_quality_flag'] = 'ANOMALOUS_VELOCITY'
    # 4. Zero movement
    df.loc[(~is_first) & (~invalid_time) & (~anom_vel) & zero_dist, 'motion_quality_flag'] = 'ZERO_MOVEMENT'
    
    # STEP 7: Generate statistics
    total_obs = len(df)
    obs_with_velocity = df['velocity_ms'].notna().sum()
    zero_movement_count = (df['motion_quality_flag'] == 'ZERO_MOVEMENT').sum()
    anomalous_velocity_count = (df['motion_quality_flag'] == 'ANOMALOUS_VELOCITY').sum()
    invalid_time_count = (df['motion_quality_flag'] == 'INVALID_TIME').sum()
    
    median_vel = df['velocity_ms'].median()
    mean_vel = df['velocity_ms'].mean()
    max_vel = df['velocity_ms'].max()
    p95_vel = df['velocity_ms'].quantile(0.95)
    
    median_disp = df['distance_m'].median()
    max_disp = df['distance_m'].max()
    
    median_time = df['time_since_previous_observation_hours'].median()
    max_time = df['time_since_previous_observation_hours'].max()
    
    print("--- OVERALL STATISTICS ---")
    print(f"Total observations: {total_obs}")
    print(f"Observations with velocity: {obs_with_velocity}")
    print(f"Zero-movement observations: {zero_movement_count}")
    print(f"Median velocity: {median_vel:.4f} m/s")
    print(f"Mean velocity: {mean_vel:.4f} m/s")
    print(f"Maximum velocity: {max_vel:.4f} m/s")
    print(f"95th percentile velocity: {p95_vel:.4f} m/s")
    print(f"Median displacement: {median_disp:.2f} m")
    print(f"Maximum displacement: {max_disp:.2f} m")
    print(f"Median time interval: {median_time} hours")
    print(f"Maximum time interval: {max_time} hours")
    print(f"Anomalous velocity count: {anomalous_velocity_count}")
    print(f"Invalid time count: {invalid_time_count}")
    
    # STEP 8: Create output
    cols_to_keep = [
        'iceberg_id', 'timestamp', 'latitude', 'longitude', 'x_m', 'y_m',
        'observation_index', 'time_since_previous_observation_hours',
        'delta_x_m', 'delta_y_m', 'distance_m', 'velocity_ms', 'velocity_kmh',
        'heading_deg', 'motion_quality_flag'
    ]
    df[cols_to_keep].to_parquet(out_parquet, index=False)
    
    # STEP 9: Create summary
    summary = df.groupby('iceberg_id').agg(
        observation_count=('observation_index', 'size'),
        moving_observation_count=('velocity_ms', lambda x: (x > 0).sum()),
        zero_movement_count=('motion_quality_flag', lambda x: (x == 'ZERO_MOVEMENT').sum()),
        mean_velocity_ms=('velocity_ms', 'mean'),
        median_velocity_ms=('velocity_ms', 'median'),
        max_velocity_ms=('velocity_ms', 'max'),
        median_distance_m=('distance_m', 'median'),
        first_observation=('timestamp', 'min'),
        last_observation=('timestamp', 'max')
    ).reset_index()
    
    summary.to_csv(out_csv, index=False)
    print("Files saved successfully.")

if __name__ == '__main__':
    process_motion()
