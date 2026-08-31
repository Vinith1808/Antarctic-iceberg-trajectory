import pytest
import numpy as np
import pandas as pd
from src.modeling.physics_baseline import get_physics_features, build_regression_dataset_A, build_regression_dataset_B

def test_vector_decomposition():
    # velocity_ms = 1.0, heading_deg = 90 (East)
    # iceberg_u should be 1.0, iceberg_v should be 0.0
    
    # Mock X shape (1, 10, 22)
    X = np.zeros((1, 10, 22))
    X[0, -1, 2] = 1.0 # vel
    X[0, -1, 3] = 90.0 # heading
    X[0, -1, 19] = 1 # current available
    X[0, -1, 20] = 1 # wind available
    X[0, -1, 21] = 1 # seaice available
    
    meta = pd.DataFrame([{'target_time_delta_hours': 1.0}])
    
    i_u, i_v, o_u, o_v, w_u, w_v, siconc, delta_t_s = get_physics_features(X, meta)
    
    assert np.isclose(i_u[0], 1.0)
    assert np.isclose(i_v[0], 0.0)
    assert delta_t_s[0] == 3600.0

def test_sea_ice_clipping():
    X = np.zeros((1, 10, 22))
    X[0, -1, 13] = 1.5 # Overshoot siconc
    X[0, -1, 21] = 1 # seaice available
    
    meta = pd.DataFrame([{'target_time_delta_hours': 1.0}])
    
    *_, siconc, _ = get_physics_features(X, meta)
    assert siconc[0] == 1.0
    
    # Missing sea ice mask
    X[0, -1, 13] = 0.5 
    X[0, -1, 21] = 0 # seaice UNavailable
    *_, siconc_missing, _ = get_physics_features(X, meta)
    assert siconc_missing[0] == 0.0

def test_missing_environmental_mask():
    X = np.zeros((1, 10, 22))
    X[0, -1, 5] = 2.0 # uo
    X[0, -1, 19] = 0 # current NOT available
    
    meta = pd.DataFrame([{'target_time_delta_hours': 1.0}])
    
    _, _, o_u, _, _, _, _, _ = get_physics_features(X, meta)
    assert o_u[0] == 0.0

def test_regression_dataset_shapes():
    o_u = np.array([1, 2])
    o_v = np.array([3, 4])
    w_u = np.array([0, 0])
    w_v = np.array([0, 0])
    i_u = np.array([1, 1])
    i_v = np.array([1, 1])
    t_u = np.array([10, 20])
    t_v = np.array([30, 40])
    
    X_A, y_A = build_regression_dataset_A(o_u, o_v, w_u, w_v, i_u, i_v, t_u, t_v)
    
    assert X_A.shape == (4, 3) # 2 samples * 2 dimensions (u, v) = 4 rows, 3 parameters (alpha, beta, gamma)
    assert y_A.shape == (4,)
    
    siconc = np.array([0.5, 0.5])
    X_B, y_B = build_regression_dataset_B(o_u, o_v, w_u, w_v, i_u, i_v, siconc, t_u, t_v)
    assert X_B.shape == (4, 3)
    assert y_B.shape == (4,)
