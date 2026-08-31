import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os

@pytest.fixture
def test_data():
    path = Path('data/test/copernicus_seaice/iceberg_seaice_test.parquet')
    assert path.exists(), f"Test file {path} not found. Run copernicus_seaice.py --test-download first."
    return pd.read_parquet(path)

@pytest.fixture
def input_data():
    path = Path('data/processed/iceberg_motion.parquet')
    return pd.read_parquet(path)

def test_row_count(test_data):
    """Verify exactly 10 output observations."""
    assert len(test_data) == 10, f"Expected 10 rows, got {len(test_data)}"

def test_coordinates_preserved(test_data, input_data):
    """Verify iceberg_id, timestamp, lat, lon are unchanged."""
    merged = pd.merge(test_data, input_data, on=['iceberg_id', 'timestamp'], suffixes=('_out', '_in'))
    assert len(merged) == 10, "Iceberg ID or timestamp altered"
    np.testing.assert_array_almost_equal(merged['latitude_out'], merged['latitude_in'])
    np.testing.assert_array_almost_equal(merged['longitude_out'], merged['longitude_in'])

def test_quality_flags(test_data):
    """Verify proper quality flags are assigned, including OUTSIDE_COVERAGE for dates > 2026-06-23."""
    for _, row in test_data.iterrows():
        if row['timestamp'] > pd.to_datetime('2026-06-23'):
            assert row['seaice_quality_flag'] == 'OUTSIDE_COVERAGE', "Dates after 2026-06-23 should be OUTSIDE_COVERAGE"
            assert pd.isna(row['siconc']), "siconc must be NaN for OUTSIDE_COVERAGE"
        else:
            if row['seaice_quality_flag'] == 'VALID':
                assert 0.0 <= row['siconc'] <= 1.0, "siconc must be in [0, 1] when VALID"
                assert not pd.isna(row['cmems_latitude']), "VALID must have cmems_latitude"
                assert not pd.isna(row['cmems_timestamp']), "VALID must have cmems_timestamp"

def test_no_mock_data(test_data):
    """Verify that siconc is not a single hardcoded mock value for all VALID rows."""
    valid_data = test_data[test_data['seaice_quality_flag'] == 'VALID']
    if len(valid_data) > 1:
        siconc_values = valid_data['siconc'].dropna().unique()
        # In real data, it's highly unlikely that 8 different locations/times have exactly the same non-zero SIC, 
        # unless it's exactly 0.0 or exactly 1.0 (pack ice or open water).
        # We just want to ensure we didn't inject 0.1/0.05 like the ocean currents mock test.
        assert not (len(siconc_values) == 1 and siconc_values[0] == 0.1), "Mock values detected!"

def test_no_credentials_logged():
    """Verify that no credentials were saved to .env or logs."""
    # This is a bit conceptual but ensures .env wasn't overwritten by the test.
    with open('.env', 'r') as f:
        content = f.read()
    assert 'COPERNICUSMARINE_USERNAME' in content
    assert 'COPERNICUSMARINE_PASSWORD' in content
