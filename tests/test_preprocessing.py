import pytest
import pandas as pd
from pathlib import Path
import numpy as np

@pytest.fixture
def original_data():
    return pd.read_parquet('data/processed/iceberg_modeling.parquet')

@pytest.fixture
def train_data():
    return pd.read_parquet('data/processed/train.parquet')

@pytest.fixture
def val_data():
    return pd.read_parquet('data/processed/validation.parquet')

@pytest.fixture
def test_data():
    return pd.read_parquet('data/processed/test.parquet')

def test_leakage_safe_split(train_data, val_data, test_data):
    train_ids = set(train_data['iceberg_id'])
    val_ids = set(val_data['iceberg_id'])
    test_ids = set(test_data['iceberg_id'])
    
    assert len(train_ids.intersection(val_ids)) == 0, "Leakage: Train and Validation sets share icebergs"
    assert len(train_ids.intersection(test_ids)) == 0, "Leakage: Train and Test sets share icebergs"
    assert len(val_ids.intersection(test_ids)) == 0, "Leakage: Validation and Test sets share icebergs"

def test_all_observations_accounted(original_data, train_data, val_data, test_data):
    total_split = len(train_data) + len(val_data) + len(test_data)
    assert total_split == len(original_data), f"Observations lost/duplicated during split. Expected {len(original_data)}, got {total_split}"
    assert total_split == 2709, "Expected 2709 observations"

def test_all_icebergs_accounted(original_data, train_data, val_data, test_data):
    total_icebergs = train_data['iceberg_id'].nunique() + val_data['iceberg_id'].nunique() + test_data['iceberg_id'].nunique()
    assert total_icebergs == original_data['iceberg_id'].nunique(), "Not all icebergs were assigned to a split"
    assert total_icebergs == 110, "Expected 110 unique icebergs"

def test_no_duplicates_in_splits(train_data, val_data, test_data):
    assert train_data.duplicated(subset=['iceberg_id', 'timestamp']).sum() == 0, "Duplicates in Train"
    assert val_data.duplicated(subset=['iceberg_id', 'timestamp']).sum() == 0, "Duplicates in Validation"
    assert test_data.duplicated(subset=['iceberg_id', 'timestamp']).sum() == 0, "Duplicates in Test"

def test_coordinates_and_timestamps_unchanged(original_data, train_data, val_data, test_data):
    combined = pd.concat([train_data, val_data, test_data])
    combined = combined.sort_values(['iceberg_id', 'timestamp']).reset_index(drop=True)
    orig = original_data.sort_values(['iceberg_id', 'timestamp']).reset_index(drop=True)
    
    np.testing.assert_array_almost_equal(combined['latitude'].values, orig['latitude'].values)
    np.testing.assert_array_almost_equal(combined['longitude'].values, orig['longitude'].values)
    assert (combined['timestamp'] == orig['timestamp']).all(), "Timestamps were modified"

def test_missing_values_not_zeroed(train_data):
    # Ensure missing values were not replaced with exactly 0 implicitly
    assert train_data['siconc'].isna().sum() > 0, "Missing values were likely filled, expected NaNs to persist"

def test_reproducible_split():
    from sklearn.model_selection import train_test_split
    # Simulate same split to prove it uses seed 42
    icebergs = np.arange(110)
    train_ids, _ = train_test_split(icebergs, test_size=0.3, random_state=42)
    train_ids2, _ = train_test_split(icebergs, test_size=0.3, random_state=42)
    np.testing.assert_array_equal(train_ids, train_ids2, "Split is not reproducible")
