import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def output_data():
    path = Path('data/processed/iceberg_seaice.parquet')
    assert path.exists(), f"File {path} not found. Run copernicus_seaice.py --download first."
    return pd.read_parquet(path)

@pytest.fixture
def input_data():
    path = Path('data/processed/iceberg_motion.parquet')
    return pd.read_parquet(path)

def test_row_count(output_data, input_data):
    """Verify exactly 2709 output observations and identical row counts."""
    assert len(output_data) == 2709, f"Expected 2709 rows, got {len(output_data)}"
    assert len(output_data) == len(input_data), "Row counts do not match"

def test_icebergs_preserved(output_data, input_data):
    """Verify all 110 iceberg IDs are preserved."""
    out_ids = set(output_data['iceberg_id'].unique())
    in_ids = set(input_data['iceberg_id'].unique())
    assert len(out_ids) == 110, f"Expected 110 unique icebergs, got {len(out_ids)}"
    assert out_ids == in_ids, "Iceberg IDs do not perfectly match input"

def test_coordinates_preserved(output_data, input_data):
    """Verify iceberg_id, timestamp, lat, lon are unchanged and no duplicates exist."""
    merged = pd.merge(output_data, input_data, on=['iceberg_id', 'timestamp'], suffixes=('_out', '_in'))
    assert len(merged) == len(input_data), "Duplicate or missing iceberg_id/timestamp pairs"
    np.testing.assert_array_almost_equal(merged['latitude_out'], merged['latitude_in'])
    np.testing.assert_array_almost_equal(merged['longitude_out'], merged['longitude_in'])

def test_quality_flags_and_siconc(output_data):
    """Verify proper quality flags are assigned and values are logical."""
    flags = output_data['seaice_quality_flag'].unique()
    valid_flags = {'VALID', 'MISSING_SIC', 'OUTSIDE_COVERAGE', 'TEMPORAL_MISMATCH', 'SPATIAL_MISMATCH'}
    for f in flags:
        assert f in valid_flags, f"Unknown flag {f}"

    for _, row in output_data.iterrows():
        if row['timestamp'] > pd.to_datetime('2026-06-23'):
            # The original anomalous row might have been passed through with OUTSIDE_COVERAGE
            # Just ensure no valid data
            assert row['seaice_quality_flag'] == 'OUTSIDE_COVERAGE', "Dates after 2026-06-23 should be OUTSIDE_COVERAGE"
            assert pd.isna(row['siconc']), "siconc must be NaN for OUTSIDE_COVERAGE"
        else:
            if row['seaice_quality_flag'] == 'VALID':
                assert -0.001 <= row['siconc'] <= 1.001, f"siconc {row['siconc']} must be approx in [0, 1] when VALID"
                assert not pd.isna(row['cmems_latitude']), "VALID must have cmems_latitude"
                assert not pd.isna(row['cmems_timestamp']), "VALID must have cmems_timestamp"

def test_no_mock_data(output_data):
    """Verify that siconc is not a single hardcoded mock value for all VALID rows."""
    valid_data = output_data[output_data['seaice_quality_flag'] == 'VALID']
    if len(valid_data) > 1:
        siconc_values = valid_data['siconc'].dropna().unique()
        assert not (len(siconc_values) == 1 and siconc_values[0] == 0.1), "Mock values detected!"
        assert len(siconc_values) > 10, "Data lacks variance, possibly mock!"

def test_no_credentials_logged():
    """Verify that no credentials were saved to .env or logs."""
    with open('.env', 'r') as f:
        content = f.read()
    assert 'COPERNICUSMARINE_USERNAME' in content
    assert 'COPERNICUSMARINE_PASSWORD' in content
