import pytest
import numpy as np
import pandas as pd
from src.modeling.regime_hybrid import RegimeHybridPredictor

@pytest.fixture
def predictor():
    pred = RegimeHybridPredictor()
    pred.middle_regime_model = 'Physics B'
    return pred

def test_missing_velocity_fallback(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = np.nan # Missing velocity
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert res['selected_model'] == 'persistence_fallback'
    assert res['regime'] == 'edge_case'
    assert res['predicted_dx_m'] == 0.0
    assert res['predicted_dy_m'] == 0.0

def test_zero_velocity_handling(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.0 # Zero velocity
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert res['selected_model'] == 'Persistence'
    assert res['regime'] == 'Stationary'
    assert res['predicted_dx_m'] == 0.0
    assert res['predicted_dy_m'] == 0.0

def test_stationary_regime(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.005 # < 0.01
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': 0.0, 'longitude': 0.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert res['selected_model'] == 'Persistence'
    assert res['regime'] == 'Stationary'

def test_metadata_preservation(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05
    seq_features[-1, 5] = 1.0
    seq_features[-1, 19] = 1
    
    meta = {
        'target_time_delta_hours': 100.0, 
        'iceberg_id': 'a23a', 
        'latitude': -65.123, 
        'longitude': 120.456,
        'target_timestamp': '2023-01-01'
    }
    
    res = predictor.predict_trajectory(seq_features, meta, 1000.0, -1000.0)
    
    assert res['iceberg_id'] == 'a23a'
    assert res['prediction_horizon_hours'] == 100.0
    assert res['original_latitude'] == -65.123
    assert res['original_longitude'] == 120.456
    assert res['timestamp'] == '2023-01-01'
    assert not np.isnan(res['predicted_latitude'])
    assert not np.isnan(res['predicted_longitude'])
    assert not np.isnan(res['predicted_dx_m'])

# --- PHASE 8.9.1 FALLBACK TESTS ---

def get_base_physics_inputs():
    seq = np.zeros((10, 22))
    seq[-1, 2] = 0.05  # velocity >= 0.03
    seq[-1, 5] = 1.0   # uo
    seq[-1, 6] = 1.0   # vo
    seq[-1, 9] = 1.0   # u10
    seq[-1, 10] = 1.0  # v10
    seq[-1, 13] = 0.5  # sic
    seq[-1, 19] = 1    # curr_avail
    seq[-1, 20] = 1    # wind_avail
    seq[-1, 21] = 1    # ice_avail
    return seq

def test_1_valid_inputs_select_physics_b(predictor):
    seq = get_base_physics_inputs()
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'Physics B'

def test_2_nan_ocean_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.nan # o_u
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_3_nan_wind_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 9] = np.nan # w_u
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_4_nan_sea_ice_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 13] = np.nan # sic
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_5_all_nan_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.nan
    seq[-1, 9] = np.nan
    seq[-1, 13] = np.nan
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_6_infinite_env_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.inf # o_u
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_7_internal_nonfinite_fallback(predictor):
    seq = get_base_physics_inputs()
    meta = {'target_time_delta_hours': np.inf, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'

def test_8_no_nans_in_fallback(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.nan
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.0, 'longitude': 45.0}
    res = predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    
    assert res['selected_model'] == 'persistence_fallback'
    assert np.isfinite(res['predicted_dx_m'])
    assert np.isfinite(res['predicted_dy_m'])
    assert np.isfinite(res['predicted_latitude'])
    assert np.isfinite(res['predicted_longitude'])

def test_9_fallback_preserves_last_coordinate(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.nan
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.123, 'longitude': 45.456}
    res = predictor.predict_trajectory(seq, meta, 100.0, 100.0)
    
    assert res['selected_model'] == 'persistence_fallback'
    assert res['predicted_dx_m'] == 0.0
    assert res['predicted_dy_m'] == 0.0
    assert res['predicted_latitude'] == -60.123
    assert res['predicted_longitude'] == 45.456

def test_10_inputs_not_mutated(predictor):
    seq = get_base_physics_inputs()
    original_seq = seq.copy()
    meta = {'target_time_delta_hours': 24.0, 'latitude': -60.123, 'longitude': 45.456}
    original_meta = meta.copy()
    
    res = predictor.predict_trajectory(seq, meta, 100.0, 100.0)
    
    assert np.array_equal(seq, original_seq)
    assert meta == original_meta
