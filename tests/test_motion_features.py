import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.preprocessing.calculate_motion import calculate_heading

def test_heading_calculation():
    # North
    assert calculate_heading(0, 10) == 0.0
    # East
    assert calculate_heading(10, 0) == 90.0
    # South
    assert calculate_heading(0, -10) == 180.0
    # West
    assert calculate_heading(-10, 0) == 270.0
    # North-East
    assert calculate_heading(10, 10) == 45.0
    # Zero-distance
    assert np.isnan(calculate_heading(0, 0))

def test_distance_and_velocity():
    # End to end logic check for velocity
    import geopandas as gpd
    
    df = pd.DataFrame({
        'iceberg_id': ['A1', 'A1'],
        'timestamp': [pd.to_datetime('2021-01-01'), pd.to_datetime('2021-01-02')],
        'latitude': [-80.0, -80.0],
        'longitude': [0.0, 1.0],  # move along parallel
        'observation_index': [0, 1],
        'time_since_previous_observation_hours': [np.nan, 24.0]
    })
    
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    ).to_crs("EPSG:3031")
    
    df['x_m'] = gdf.geometry.x
    df['y_m'] = gdf.geometry.y
    
    # Distance
    dx = df['x_m'].iloc[1] - df['x_m'].iloc[0]
    dy = df['y_m'].iloc[1] - df['y_m'].iloc[0]
    dist = np.sqrt(dx**2 + dy**2)
    
    assert dist > 0
    
    # Velocity
    vel_ms = dist / (24.0 * 3600)
    assert vel_ms > 0
