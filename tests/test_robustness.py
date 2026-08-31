import pytest
import numpy as np
from src.modeling.regime_hybrid import RegimeHybridPredictor

@pytest.fixture
def predictor():
    pred = RegimeHybridPredictor()
    pred.middle_regime_model = 'Persistence'
    return pred

def test_missing_environment_robustness(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05 # Moving => uses Physics B
    # Missing ocean
    seq_features[-1, 5:9] = np.nan
    seq_features[-1, 19] = 1.0 # Force NaN to propagate
    # Missing wind
    seq_features[-1, 9:13] = np.nan
    seq_features[-1, 20] = 1.0 # Force NaN to propagate
    # Missing sea ice
    seq_features[-1, 13] = np.nan
    seq_features[-1, 21] = 1.0 # Force NaN to propagate
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert res['selected_model'] == 'persistence_fallback'
    assert not np.isnan(res['predicted_latitude'])
    assert not np.isnan(res['predicted_longitude'])

def test_physical_sanity_bounds(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05 # Moving
    # Valid environment
    seq_features[-1, 5] = 1.0 # o_u
    seq_features[-1, 19] = 1 # current available
    
    # Position at North Pole boundary just to test latitude bounds (though it's Antarctic data)
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -89.0, 'longitude': 179.0}
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert -90 <= res['predicted_latitude'] <= 90
    assert -180 <= res['predicted_longitude'] <= 180

def test_no_modification_of_inputs(predictor):
    seq_features = np.zeros((10, 22))
    seq_features[-1, 2] = 0.05
    original_seq = seq_features.copy()
    
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    original_meta = meta.copy()
    
    res = predictor.predict_trajectory(seq_features, meta, 0.0, 0.0)
    
    assert np.array_equal(seq_features, original_seq)
    assert meta == original_meta
