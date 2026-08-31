import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def original_data():
    return pd.read_parquet('data/processed/iceberg_motion.parquet')

@pytest.fixture
def extracted_data():
    path = Path('data/processed/iceberg_wind.parquet')
    if not path.exists():
        pytest.skip("Production ERA5 data not found.")
    return pd.read_parquet(path)

def test_row_preservation(original_data, extracted_data):
    """Output row count should match the original exactly."""
    assert len(extracted_data) == len(original_data), "Row count changed."

def test_coordinate_preservation(original_data, extracted_data):
    """Original latitude/longitude should remain unchanged."""
    merged = extracted_data.merge(
        original_data[['iceberg_id', 'timestamp', 'latitude', 'longitude']],
        on=['iceberg_id', 'timestamp'],
        suffixes=('', '_orig')
    )
    pd.testing.assert_series_equal(merged['latitude'], merged['latitude_orig'], check_names=False)
    pd.testing.assert_series_equal(merged['longitude'], merged['longitude_orig'], check_names=False)

def test_wind_speed_calculation(extracted_data):
    """Speed should be sqrt(u10^2 + v10^2)."""
    valid = extracted_data[extracted_data['wind_quality_flag'] == 'VALID']
    expected_speed = np.sqrt(valid['u10']**2 + valid['v10']**2)
    pd.testing.assert_series_equal(valid['wind_speed_ms'], expected_speed, check_names=False)

def test_wind_direction_calculation(extracted_data):
    """Direction should be arctan2(u10, v10) % 360."""
    valid = extracted_data[extracted_data['wind_quality_flag'] == 'VALID']
    expected_direction = np.degrees(np.arctan2(valid['u10'], valid['v10'])) % 360
    pd.testing.assert_series_equal(valid['wind_direction_deg'], expected_direction, check_names=False)

def test_no_credentials_leaked(extracted_data):
    """Ensure no credential columns exist."""
    expected_cols = [
        'iceberg_id', 'timestamp', 'latitude', 'longitude', 'u10', 'v10', 
        'wind_speed_ms', 'wind_direction_deg', 'era5_timestamp', 
        'era5_latitude', 'era5_longitude', 'wind_quality_flag'
    ]
    for col in extracted_data.columns:
        assert col in expected_cols, f"Unexpected column {col} found."
