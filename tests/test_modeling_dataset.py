import pytest
import pandas as pd
from pathlib import Path
import numpy as np

@pytest.fixture
def modeling_data():
    path = Path('data/processed/iceberg_modeling.parquet')
    assert path.exists(), "Modeling dataset not found."
    return pd.read_parquet(path)

@pytest.fixture
def motion_data():
    return pd.read_parquet('data/processed/iceberg_motion.parquet')

def test_row_count_preserved(modeling_data, motion_data):
    assert len(modeling_data) == len(motion_data), "Row count changed after merge"
    assert len(modeling_data) == 2709, "Expected 2709 rows"

def test_unique_icebergs_preserved(modeling_data, motion_data):
    assert modeling_data['iceberg_id'].nunique() == motion_data['iceberg_id'].nunique()
    assert modeling_data['iceberg_id'].nunique() == 110, "Expected 110 icebergs"

def test_no_duplicates(modeling_data):
    dupes = modeling_data.duplicated(subset=['iceberg_id', 'timestamp']).sum()
    assert dupes == 0, "Found duplicate iceberg_id + timestamp pairs"

def test_coordinates_unchanged(modeling_data, motion_data):
    # Since they are left-joined, the order might be different if not sorted,
    # but build_modeling_dataset.py sorts by iceberg_id and timestamp.
    # We should merge to compare properly.
    merged = pd.merge(modeling_data, motion_data, on=['iceberg_id', 'timestamp'], suffixes=('_mod', '_mot'))
    np.testing.assert_array_equal(merged['latitude_mod'], merged['latitude_mot'])
    np.testing.assert_array_equal(merged['longitude_mod'], merged['longitude_mot'])

def test_chronological_ordering(modeling_data):
    for iceberg_id, group in modeling_data.groupby('iceberg_id'):
        assert group['timestamp'].is_monotonic_increasing, f"Iceberg {iceberg_id} not strictly chronologically ordered"

def test_time_features(modeling_data):
    assert 'year' in modeling_data.columns
    assert 'month' in modeling_data.columns
    assert 'day_of_year' in modeling_data.columns
    assert 'day_of_week' in modeling_data.columns
    assert 'hour' in modeling_data.columns
    assert 'days_since_previous_observation' in modeling_data.columns
    
    # Spot check one derivation
    np.testing.assert_array_equal(modeling_data['year'], modeling_data['timestamp'].dt.year)
    
def test_availability_flags(modeling_data):
    assert 'current_available' in modeling_data.columns
    assert 'wind_available' in modeling_data.columns
    assert 'seaice_available' in modeling_data.columns
    
    # Verify mapping logic
    assert ((modeling_data['current_quality_flag'] == 'VALID') == (modeling_data['current_available'] == 1)).all()
    assert ((modeling_data['wind_quality_flag'] == 'VALID') == (modeling_data['wind_available'] == 1)).all()
    assert ((modeling_data['seaice_quality_flag'] == 'VALID') == (modeling_data['seaice_available'] == 1)).all()

def test_no_unnecessary_columns(modeling_data):
    # Ensure raw coordinates from env datasets were not included
    assert 'copernicus_latitude' not in modeling_data.columns
    assert 'era5_latitude' not in modeling_data.columns
    assert 'cmems_latitude' not in modeling_data.columns
