import pytest
import numpy as np
import pandas as pd
from src.modeling.multi_horizon import MultiHorizonPredictor

@pytest.fixture
def predictor():
    pred = MultiHorizonPredictor()
    pred.predictor.middle_regime_model = 'Persistence'
    return pred

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

def test_multi_horizon_generation(predictor):
    seq = get_base_physics_inputs()
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    assert len(res) == 5
    assert res[0]['horizon_hours'] == 24.0
    assert res[1]['horizon_hours'] == 72.0
    assert res[2]['horizon_hours'] == 168.0
    assert res[3]['horizon_hours'] == 240.0
    assert res[4]['horizon_hours'] == 720.0

def test_original_coordinates_not_modified(predictor):
    seq = get_base_physics_inputs()
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    original_meta = meta.copy()
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    assert meta == original_meta

def test_no_nan_or_inf(predictor):
    seq = get_base_physics_inputs()
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    for r in res:
        assert np.isfinite(r['predicted_dx_m'])
        assert np.isfinite(r['predicted_dy_m'])
        assert np.isfinite(r['predicted_latitude'])
        assert np.isfinite(r['predicted_longitude'])

def test_missing_input_fallback_does_not_crash(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 5] = np.nan # o_u
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    for r in res:
        assert r['selected_model'] == 'persistence_fallback'
        assert r['prediction_quality'] == 'degraded'
        assert r['fallback_used'] is True
        assert np.isfinite(r['predicted_latitude'])

def test_threshold_preserved(predictor):
    seq = get_base_physics_inputs()
    seq[-1, 2] = 0.01 # < 0.03
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    for r in res:
        assert r['selected_model'] == 'Persistence'
        assert r['predicted_dx_m'] == 0.0
        assert r['predicted_dy_m'] == 0.0

def test_bounds_and_valid_values(predictor):
    seq = get_base_physics_inputs()
    meta = {'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_multi_horizon(seq, meta, 0.0, 0.0)
    
    for r in res:
        assert -90 <= r['predicted_latitude'] <= 90
        assert -180 <= r['predicted_longitude'] <= 180
