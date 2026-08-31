import pytest
import numpy as np
import yaml
from pathlib import Path
from src.modeling.regime_hybrid import RegimeHybridPredictor

@pytest.fixture
def predictor():
    pred = RegimeHybridPredictor()
    # Force the selected middle regime model as per validation results
    pred.middle_regime_model = 'Persistence' 
    return pred

def test_final_threshold_configuration(predictor):
    # Verify threshold is exactly 0.03 for Physics B as per Phase 8.7 validation
    assert predictor.T_high == 0.03
    # And since middle_regime is Persistence, everything < 0.03 goes to Persistence
    
    with open('config/trajectory_model.yaml', 'r') as f:
        config = yaml.safe_load(f)
    assert config['stationary_slow_threshold_ms'] == 0.03
    assert config['low_speed_regime_model'] == 'persistence'
    assert config['high_speed_regime_model'] == 'physics_b'

def test_below_threshold_selects_persistence(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.029 # < 0.03
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    assert res['selected_model'] == 'Persistence'
    
def test_at_threshold_selects_physics_b(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.030 # >= 0.03
    seq_features[-1, 5] = 1.0 # mock valid env
    seq_features[-1, 19] = 1
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    assert res['selected_model'] == 'Physics B'

def test_missing_velocity_fallback(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = np.nan
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
def test_output_schema(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.0
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'schema_test', 'latitude': -60.0, 'longitude': 45.0, 'target_timestamp': '2023-01-01'}
    
    res = predictor.predict_trajectory(seq_features, meta, 1000.0, 1000.0)
    
    expected_keys = {
        'iceberg_id', 'timestamp', 'original_latitude', 'original_longitude',
        'prediction_horizon_hours', 'predicted_dx_m', 'predicted_dy_m',
        'predicted_latitude', 'predicted_longitude', 'regime', 'selected_model'
    }
    
    assert set(res.keys()) == expected_keys
    assert res['original_latitude'] == -60.0
    assert res['original_longitude'] == 45.0
    
def test_no_original_coordinates_modified(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05
    seq_features[-1, 5] = 1.0
    seq_features[-1, 19] = 1
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 1000.0, 1000.0)
    
    assert meta['latitude'] == -60.0
    assert meta['longitude'] == 45.0
    assert res['original_latitude'] == -60.0
    
def test_no_nans_in_valid_predictions(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05
    seq_features[-1, 5] = 1.0
    seq_features[-1, 19] = 1
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0, 'target_timestamp': '2023-01-01'}
    
    res = predictor.predict_trajectory(seq_features, meta, 1000.0, 1000.0)
    
    assert not np.isnan(res['predicted_dx_m'])
    assert not np.isnan(res['predicted_dy_m'])
    assert not np.isnan(res['predicted_latitude'])
    assert not np.isnan(res['predicted_longitude'])
