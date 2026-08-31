from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class TrajectoryRequest(BaseModel):
    iceberg_id: str = Field(..., description="Unique identifier for the iceberg")
    timestamp: datetime.datetime = Field(..., description="Observation timestamp")
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    velocity_ms: float = Field(..., ge=0, description="Iceberg velocity magnitude in m/s")
    heading_deg: float = Field(..., description="Iceberg heading in degrees")
    
    # Environmental variables (can be None or NaN)
    uo: Optional[float] = Field(None, description="Ocean current u-component (m/s)")
    vo: Optional[float] = Field(None, description="Ocean current v-component (m/s)")
    u10: Optional[float] = Field(None, description="10m wind u-component (m/s)")
    v10: Optional[float] = Field(None, description="10m wind v-component (m/s)")
    siconc: Optional[float] = Field(None, description="Sea ice concentration (0-1)")

class Prediction(BaseModel):
    horizon_hours: float = Field(..., description="Prediction horizon in hours")
    predicted_dx_m: float = Field(..., description="Predicted displacement in x (meters, EPSG:3031)")
    predicted_dy_m: float = Field(..., description="Predicted displacement in y (meters, EPSG:3031)")
    predicted_latitude: float = Field(..., description="Predicted latitude")
    predicted_longitude: float = Field(..., description="Predicted longitude")
    selected_model: str = Field(..., description="The internal model selected for this prediction")
    fallback_used: bool = Field(..., description="True if fallback logic was triggered")
    prediction_quality: str = Field(..., description="Quality of prediction (nominal/degraded)")

class TrajectoryResponse(BaseModel):
    iceberg_id: str
    input_timestamp: datetime.datetime
    predictions: List[Prediction]

class HealthResponse(BaseModel):
    status: str
    service: str
    model: str
    multi_horizon: bool
    supported_horizons_hours: List[float]

class ModelInfoResponse(BaseModel):
    model: str
    low_speed_model: str
    high_speed_model: str
    threshold_ms: float
    supported_horizons: List[float]
