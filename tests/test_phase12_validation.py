import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

from src.modeling.regime_hybrid import RegimeHybridPredictor
from src.modeling.multi_horizon import MultiHorizonPredictor
from src.api.trajectory_api import app

def test_regime_boundaries():
    predictor = RegimeHybridPredictor()
    predictor.fit_validation_policy() # Properly sets middle regime model
    # Mock data
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    def get_seq(vel):
        seq = np.zeros((10, 22))
        seq[-1, 2] = vel
        # ensure environmental vars are finite and "available"
        seq[-1, 19] = 1.0; seq[-1, 5:7] = 0.1 # ocean
        seq[-1, 20] = 1.0; seq[-1, 9:11] = 0.1 # wind
        seq[-1, 21] = 1.0; seq[-1, 13] = 0.1 # sea ice
        return seq
        
    test_cases = [
        (0.0, 'Persistence'),
        (0.009, 'Persistence'),
        (0.01, 'Persistence'),
        (0.029999, 'Persistence'),
        (0.03, 'Physics B'),
        (0.030001, 'Physics B'),
        (0.10, 'Physics B'),
    ]
    
    for vel, expected_model in test_cases:
        res = predictor.predict_trajectory(get_seq(vel), meta, 0.0, 0.0)
        assert res['selected_model'] == expected_model, f"Failed for velocity {vel}: got {res['selected_model']}, expected {expected_model}"

def test_multi_horizon_inference():
    mh = MultiHorizonPredictor()
    meta = {'target_timestamp': pd.Timestamp('2023-01-01'), 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    seq = np.zeros((10, 22))
    seq[-1, 2] = 0.05 # Physics B
    seq[-1, 19] = 1.0; seq[-1, 5:7] = 0.1
    seq[-1, 20] = 1.0; seq[-1, 9:11] = 0.1
    seq[-1, 21] = 1.0; seq[-1, 13] = 0.1
    
    res = mh.predict_multi_horizon(seq, meta, 0.0, 0.0)
    assert len(res) == 5
    
    expected_horizons = [24.0, 72.0, 168.0, 240.0, 720.0]
    actual_horizons = [r['horizon_hours'] for r in res]
    assert actual_horizons == expected_horizons
    
    for r in res:
        assert np.isfinite(r['predicted_dx_m'])
        assert np.isfinite(r['predicted_dy_m'])
        assert -90 <= r['predicted_latitude'] <= 90
        assert -180 <= r['predicted_longitude'] <= 180
        assert r['selected_model'] == 'Physics B'
        assert isinstance(r['fallback_used'], bool)
        assert not r['fallback_used']

def test_safety_fallback():
    predictor = RegimeHybridPredictor()
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    
    def get_base_seq():
        seq = np.zeros((10, 22))
        seq[-1, 2] = 0.05 # Moving => should trigger Physics B normally
        seq[-1, 19] = 1.0; seq[-1, 5:7] = 0.1
        seq[-1, 20] = 1.0; seq[-1, 9:11] = 0.1
        seq[-1, 21] = 1.0; seq[-1, 13] = 0.1
        return seq

    # A. Missing ocean current
    seqA = get_base_seq(); seqA[-1, 5] = np.nan
    res = predictor.predict_trajectory(seqA, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
    # B. Missing wind
    seqB = get_base_seq(); seqB[-1, 9] = np.nan
    res = predictor.predict_trajectory(seqB, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
    # C. Missing sea-ice
    seqC = get_base_seq(); seqC[-1, 13] = np.nan
    res = predictor.predict_trajectory(seqC, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
    # D/E. Infinity environmental value
    seqE = get_base_seq(); seqE[-1, 5] = np.inf
    res = predictor.predict_trajectory(seqE, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
    # F. Multiple missing
    seqF = get_base_seq(); seqF[-1, 5] = np.nan; seqF[-1, 9] = np.nan
    res = predictor.predict_trajectory(seqF, meta, 0.0, 0.0)
    assert res['selected_model'] == 'persistence_fallback'
    
    # Check outputs are finite and default to origin
    assert res['predicted_dx_m'] == 0.0
    assert res['predicted_dy_m'] == 0.0
    assert res['predicted_latitude'] == meta['latitude']
    assert res['predicted_longitude'] == meta['longitude']

def test_input_immutability():
    predictor = RegimeHybridPredictor()
    meta = {'target_time_delta_hours': 24.0, 'iceberg_id': 'test', 'latitude': -60.0, 'longitude': 45.0}
    seq = np.zeros((10, 22))
    seq[-1, 2] = 0.05
    seq[-1, 19] = 1.0; seq[-1, 5:7] = 0.1
    seq[-1, 20] = 1.0; seq[-1, 9:11] = 0.1
    seq[-1, 21] = 1.0; seq[-1, 13] = 0.1
    
    seq_copy = seq.copy()
    meta_copy = meta.copy()
    
    predictor.predict_trajectory(seq, meta, 0.0, 0.0)
    
    assert np.array_equal(seq, seq_copy, equal_nan=True)
    assert meta == meta_copy

def test_api_validation():
    client = TestClient(app)
    
    # Health & Info
    assert client.get("/health").status_code == 200
    assert client.get("/model/info").status_code == 200
    
    base_payload = {
        "iceberg_id": "test_iceberg",
        "timestamp": "2023-01-01T12:00:00Z",
        "latitude": -65.0, "longitude": 45.0,
        "velocity_ms": 0.05, "heading_deg": 180.0,
        "uo": 0.1, "vo": -0.1, "u10": 5.0, "v10": -5.0, "siconc": 0.5
    }
    
    # 1. Normal moving
    r = client.post("/predict/trajectory", json=base_payload)
    assert r.status_code == 200
    assert r.json()["predictions"][0]["selected_model"] == "Physics B"
    
    # 2. Stationary
    p = base_payload.copy(); p["velocity_ms"] = 0.0
    assert client.post("/predict/trajectory", json=p).json()["predictions"][0]["selected_model"] == "Persistence"
    
    # 3. Slow-moving
    p = base_payload.copy(); p["velocity_ms"] = 0.02
    assert client.post("/predict/trajectory", json=p).json()["predictions"][0]["selected_model"] == "Persistence"
    
    # 4. Exactly 0.03
    p = base_payload.copy(); p["velocity_ms"] = 0.03
    assert client.post("/predict/trajectory", json=p).json()["predictions"][0]["selected_model"] == "Physics B"
    
    # 5/6. Missing / NaN
    p = base_payload.copy(); del p["u10"]
    assert client.post("/predict/trajectory", json=p).json()["predictions"][0]["selected_model"] == "persistence_fallback"
    
    # 7. Invalid lat
    p = base_payload.copy(); p["latitude"] = -100
    assert client.post("/predict/trajectory", json=p).status_code == 422
    
    # 8. Invalid lon
    p = base_payload.copy(); p["longitude"] = 200
    assert client.post("/predict/trajectory", json=p).status_code == 422
    
    # 9. Invalid velocity
    p = base_payload.copy(); p["velocity_ms"] = -1.0
    assert client.post("/predict/trajectory", json=p).status_code == 422
    
    # 10. Malformed
    assert client.post("/predict/trajectory", json={"bad": "request"}).status_code == 422

def test_model_artifacts():
    paths = [
        'models/checkpoints/lstm_baseline_best.pt',
        'models/preprocessing/scaler.pkl',
        'models/preprocessing/target_scaler.pkl',
        'config/trajectory_model.yaml'
    ]
    for p in paths:
        assert Path(p).exists(), f"Artifact missing: {p}"

def test_data_integrity():
    train_meta = pd.read_parquet('data/processed/sequences/train_meta.parquet')
    val_meta = pd.read_parquet('data/processed/sequences/validation_meta.parquet')
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    train_ids = set(train_meta['iceberg_id'].unique())
    val_ids = set(val_meta['iceberg_id'].unique())
    test_ids = set(test_meta['iceberg_id'].unique())
    
    # No duplicate IDs across splits
    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0
