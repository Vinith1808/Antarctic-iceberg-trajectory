import pytest
from fastapi.testclient import TestClient
import numpy as np
import datetime

from src.api.trajectory_api import app

client = TestClient(app)

def get_valid_payload(velocity_ms=0.05):
    return {
        "iceberg_id": "test_iceberg",
        "timestamp": "2023-01-01T12:00:00Z",
        "latitude": -65.0,
        "longitude": 45.0,
        "velocity_ms": velocity_ms,
        "heading_deg": 180.0,
        "uo": 0.1,
        "vo": -0.1,
        "u10": 5.0,
        "v10": -5.0,
        "siconc": 0.5
    }

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "regime_hybrid" in data["model"]
    assert 24.0 in data["supported_horizons_hours"]

def test_model_info():
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["threshold_ms"] == 0.03

def test_valid_trajectory_request():
    payload = get_valid_payload()
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["iceberg_id"] == "test_iceberg"
    assert len(data["predictions"]) == 5
    
    horizons = [p["horizon_hours"] for p in data["predictions"]]
    assert horizons == [24.0, 72.0, 168.0, 240.0, 720.0]
    
    for p in data["predictions"]:
        assert -90 <= p["predicted_latitude"] <= 90
        assert -180 <= p["predicted_longitude"] <= 180
        assert p["selected_model"] == "Physics B"
        assert p["fallback_used"] is False

def test_zero_velocity():
    payload = get_valid_payload(velocity_ms=0.0)
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    for p in data["predictions"]:
        assert p["selected_model"] == "Persistence"
        assert p["predicted_latitude"] == payload["latitude"]

def test_boundary_policy():
    # Exactly 0.03 -> high speed
    payload = get_valid_payload(velocity_ms=0.03)
    response = client.post("/predict/trajectory", json=payload)
    assert response.json()["predictions"][0]["selected_model"] == "Physics B"
    
    # Just below 0.03 -> Persistence
    payload = get_valid_payload(velocity_ms=0.029)
    response = client.post("/predict/trajectory", json=payload)
    assert response.json()["predictions"][0]["selected_model"] == "Persistence"

def test_missing_wind_triggers_fallback():
    payload = get_valid_payload()
    del payload["u10"] # missing
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 200
    data = response.json()
    for p in data["predictions"]:
        assert p["selected_model"] == "persistence_fallback"
        assert p["fallback_used"] is True
        assert p["prediction_quality"] == "degraded"

def test_missing_ocean_triggers_fallback():
    payload = get_valid_payload()
    payload["uo"] = None # None via JSON -> null
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 200
    data = response.json()
    for p in data["predictions"]:
        assert p["selected_model"] == "persistence_fallback"
        assert p["fallback_used"] is True

def test_missing_sea_ice_triggers_fallback():
    payload = get_valid_payload()
    payload["siconc"] = None
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 200
    assert response.json()["predictions"][0]["selected_model"] == "persistence_fallback"

def test_invalid_latitude():
    payload = get_valid_payload()
    payload["latitude"] = -95.0
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 422 # Unprocessable Entity (Pydantic Validation)

def test_invalid_longitude():
    payload = get_valid_payload()
    payload["longitude"] = "this_is_not_a_number"
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 422

def test_invalid_velocity():
    payload = get_valid_payload()
    payload["velocity_ms"] = -0.5
    
    response = client.post("/predict/trajectory", json=payload)
    assert response.status_code == 422
