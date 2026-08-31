import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def original_data():
    return pd.read_parquet('data/processed/iceberg_motion.parquet')

@pytest.fixture
def extracted_data():
    path = Path('data/processed/iceberg_currents.parquet')
    if not path.exists():
        pytest.skip("Extracted currents data not found.")
    return pd.read_parquet(path)

def test_row_preservation(original_data, extracted_data):
    """Output row count should match input row count after excluding anomalous motion."""
    original_valid = original_data[original_data['motion_quality_flag'] != 'ANOMALOUS_VELOCITY']
    assert len(extracted_data) == len(original_valid), "Row count changed."
    assert extracted_data['iceberg_id'].nunique() == original_valid['iceberg_id'].nunique(), "Unique iceberg count changed."

def test_coordinate_preservation(original_data, extracted_data):
    """Original latitude/longitude should remain unchanged."""
    merged = extracted_data.merge(
        original_data[['iceberg_id', 'timestamp', 'latitude', 'longitude']],
        on=['iceberg_id', 'timestamp'],
        suffixes=('', '_orig')
    )
    pd.testing.assert_series_equal(merged['latitude'], merged['latitude_orig'], check_names=False)
    pd.testing.assert_series_equal(merged['longitude'], merged['longitude_orig'], check_names=False)

def test_duplicate_detection(extracted_data):
    """No duplicate iceberg_id + timestamp rows."""
    duplicates = extracted_data.duplicated(subset=['iceberg_id', 'timestamp'])
    assert duplicates.sum() == 0, "Duplicate rows detected."

def test_current_speed_calculation(extracted_data):
    """Speed should be sqrt(uo^2 + vo^2)."""
    valid = extracted_data[extracted_data['current_quality_flag'] == 'VALID']
    expected_speed = np.sqrt(valid['uo']**2 + valid['vo']**2)
    pd.testing.assert_series_equal(valid['current_speed_ms'], expected_speed, check_names=False)

def test_current_direction_calculation(extracted_data):
    """Direction should be arctan2(uo, vo) % 360."""
    valid = extracted_data[extracted_data['current_quality_flag'] == 'VALID']
    expected_direction = np.degrees(np.arctan2(valid['uo'], valid['vo'])) % 360
    pd.testing.assert_series_equal(valid['current_direction_deg'], expected_direction, check_names=False)

def test_quality_flags(extracted_data):
    """Check flag logic."""
    valid = extracted_data[extracted_data['current_quality_flag'] == 'VALID']
    assert valid['uo'].isna().sum() == 0
    assert valid['vo'].isna().sum() == 0
    assert valid['current_speed_ms'].isna().sum() == 0
    
    missing = extracted_data[extracted_data['current_quality_flag'] == 'MISSING_CURRENT']
    if not missing.empty:
        assert missing['uo'].isna().all()
        
def test_no_credentials_leaked(extracted_data):
    """Sanity check to ensure no weird columns exist that could be creds."""
    expected_cols = [
        'iceberg_id', 'timestamp', 'latitude', 'longitude', 'uo', 'vo', 
        'current_speed_ms', 'current_direction_deg', 'copernicus_timestamp', 
        'copernicus_latitude', 'copernicus_longitude', 'surface_depth_m', 
        'current_quality_flag'
    ]
    for col in extracted_data.columns:
        assert col in expected_cols, f"Unexpected column {col} found."
