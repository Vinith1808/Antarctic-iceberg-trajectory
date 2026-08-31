from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.api.schemas import (
    TrajectoryRequest, 
    TrajectoryResponse, 
    Prediction, 
    HealthResponse, 
    ModelInfoResponse
)
from src.modeling.multi_horizon import MultiHorizonPredictor

app = FastAPI(
    title="Antarctic Iceberg Trajectory Predictor API",
    description="Integration-Ready API for multi-horizon iceberg trajectory prediction.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Predictor Instance
# Loaded once at startup to keep requests lightweight
try:
    predictor = MultiHorizonPredictor()
    predictor.predictor.middle_regime_model = 'Persistence'
except Exception as e:
    print(f"Error initializing predictor: {e}")
    predictor = None

def convert_request_to_model_inputs(req: TrajectoryRequest):
    """Converts the Pydantic schema to the inputs required by the underlying predictor."""
    # 1. Reconstruct sequence_X_phys (shape: [10, 22])
    # The models only use the final observation (-1 index)
    seq = np.zeros((10, 22))
    
    seq[-1, 2] = req.velocity_ms
    seq[-1, 3] = req.heading_deg
    
    seq[-1, 5] = req.uo if req.uo is not None else np.nan
    seq[-1, 6] = req.vo if req.vo is not None else np.nan
    seq[-1, 19] = 1.0  # Force 1.0 so NaN propagates to trigger fallback
    
    seq[-1, 9] = req.u10 if req.u10 is not None else np.nan
    seq[-1, 10] = req.v10 if req.v10 is not None else np.nan
    seq[-1, 20] = 1.0  # Force 1.0 so NaN propagates
    
    seq[-1, 13] = req.siconc if req.siconc is not None else np.nan
    seq[-1, 21] = 1.0  # Force 1.0 so NaN propagates
    
    # 2. Meta row
    meta_row = {
        'iceberg_id': req.iceberg_id,
        'timestamp': req.timestamp,
        'latitude': req.latitude,
        'longitude': req.longitude
    }
    
    # 3. Project to EPSG:3031
    gdf = gpd.GeoDataFrame(
        geometry=[Point(req.longitude, req.latitude)],
        crs="EPSG:4326"
    )
    gdf_3031 = gdf.to_crs("EPSG:3031")
    x_m = gdf_3031.geometry.x.iloc[0]
    y_m = gdf_3031.geometry.y.iloc[0]
    
    return seq, meta_row, x_m, y_m

@app.get("/health", response_model=HealthResponse)
def health_check():
    if predictor is None:
        raise HTTPException(status_code=500, detail="Model initialization failed")
        
    return HealthResponse(
        status="healthy",
        service="antarctic-iceberg-trajectory-predictor",
        model="regime_hybrid",
        multi_horizon=True,
        supported_horizons_hours=predictor.horizons
    )

@app.get("/model/info", response_model=ModelInfoResponse)
def model_info():
    if predictor is None:
        raise HTTPException(status_code=500, detail="Model initialization failed")
        
    return ModelInfoResponse(
        model="regime_hybrid",
        low_speed_model="persistence",
        high_speed_model="physics_b",
        threshold_ms=0.03,
        supported_horizons=predictor.horizons
    )

@app.post("/predict/trajectory", response_model=TrajectoryResponse)
def predict_trajectory(request: TrajectoryRequest):
    if predictor is None:
        raise HTTPException(status_code=500, detail="Predictor not initialized")
        
    # Validation constraint from Phase 8.9.1 guarantees NaN inputs fallback safely.
    # We pass the NaNs down.
    
    try:
        seq, meta_row, x_m, y_m = convert_request_to_model_inputs(request)
        
        # Predict
        raw_predictions = predictor.predict_multi_horizon(seq, meta_row, x_m, y_m)
        
        # Convert to API response
        api_predictions = []
        for r in raw_predictions:
            # Final check against NaN coordinates just to fulfill the API strictness contract
            if not np.isfinite(r['predicted_latitude']) or not np.isfinite(r['predicted_longitude']):
                raise ValueError("Prediction produced non-finite coordinates.")
                
            api_predictions.append(Prediction(
                horizon_hours=r['horizon_hours'],
                predicted_dx_m=r['predicted_dx_m'],
                predicted_dy_m=r['predicted_dy_m'],
                predicted_latitude=r['predicted_latitude'],
                predicted_longitude=r['predicted_longitude'],
                selected_model=r['selected_model'],
                fallback_used=r['fallback_used'],
                prediction_quality=r['prediction_quality']
            ))
            
        return TrajectoryResponse(
            iceberg_id=request.iceberg_id,
            input_timestamp=request.timestamp,
            predictions=api_predictions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")
