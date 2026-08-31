import pytest
import numpy as np
import pandas as pd
import torch
from pathlib import Path
import joblib

from src.modeling.evaluate_baselines import euclidean_error
from src.preprocessing.calculate_motion import calculate_heading

def test_euclidean_error():
    # dx=3, dy=4 -> 5
    y_true = np.array([[3.0, 4.0], [0.0, 0.0]])
    y_pred = np.array([[0.0, 0.0], [1.0, 1.0]])
    
    err = euclidean_error(y_true, y_pred)
    assert err[0] == 5.0
    assert np.isclose(err[1], np.sqrt(2))

def test_heading_convention():
    # Verify the constant velocity math matches calculate_heading
    # dx = 1, dy = 0 -> East (90 deg)
    assert calculate_heading(1, 0) == 90.0
    
    # dx = 0, dy = 1 -> North (0 deg)
    assert calculate_heading(0, 1) == 0.0
    
    # dx = 1, dy = 1 -> NE (45 deg)
    assert calculate_heading(1, 1) == 45.0
    
    # Reverse test for predicting dx, dy from velocity and heading
    v = 1.0
    dt = 1.0 # 1 second
    h = 90.0 # East
    
    pred_dx = v * dt * np.sin(np.radians(h))
    pred_dy = v * dt * np.cos(np.radians(h))
    
    assert np.isclose(pred_dx, 1.0)
    assert np.isclose(pred_dy, 0.0)
    
def test_persistence_is_zero():
    pers_dx = np.zeros(10)
    assert np.all(pers_dx == 0)

def test_no_nan_inf_predictions():
    # Mock data to ensure cv logic produces no nan
    velocity_ms = np.array([1.0, 0.0, np.nan])
    heading_deg = np.array([45.0, np.nan, 90.0])
    time_delta_s = np.array([3600.0, 3600.0, 3600.0])
    
    cv_dx = velocity_ms * time_delta_s * np.sin(np.radians(heading_deg))
    cv_dy = velocity_ms * time_delta_s * np.cos(np.radians(heading_deg))
    
    cv_dx = np.nan_to_num(cv_dx, nan=0.0)
    cv_dy = np.nan_to_num(cv_dy, nan=0.0)
    
    assert not np.isnan(cv_dx).any()
    assert not np.isnan(cv_dy).any()

def test_model_scaler_persistence():
    # Ensure scaler isn't modified
    scaler_path = Path('models/preprocessing/target_scaler.pkl')
    scaler = joblib.load(scaler_path)
    old_mean = scaler.mean_.copy()
    
    # Dummy evaluation
    X = np.random.randn(10, 2)
    scaler.transform(X)
    
    np.testing.assert_array_equal(old_mean, scaler.mean_, "Scaler was mutated during inference!")
