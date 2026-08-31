import pytest
import pandas as pd
import numpy as np
import datetime
from src.api.schemas import TrajectoryRequest
from src.api.trajectory_api import convert_request_to_model_inputs
from src.modeling.multi_horizon import MultiHorizonPredictor

@pytest.fixture(scope="module")
def latest_observations():
    df = pd.read_parquet('data/processed/iceberg_modeling.parquet')
    df = df.sort_values(['iceberg_id', 'timestamp'])
    return df.groupby('iceberg_id').last().reset_index()

@pytest.fixture(scope="module")
def predictor():
    pred = MultiHorizonPredictor()
    pred.predictor.middle_regime_model = 'Persistence'
    return pred

def test_all_icebergs_discovered(latest_observations):
    """1. All iceberg IDs are discovered."""
    assert len(latest_observations) == 110
    assert latest_observations['iceberg_id'].nunique() == 110

def test_every_iceberg_predictions(latest_observations, predictor):
    """
    2. Every iceberg receives five horizons.
    3. Expected maximum output is 550 rows.
    4. No prediction contains NaN.
    5. No prediction contains Infinity.
    6. Coordinates remain within valid geographic bounds.
    7. Input observations remain unchanged.
    8. Missing environmental values trigger safe fallback.
    9. Model routing remains consistent with the existing 0.03 m/s policy.
    """
    total_predictions = 0
    
    for _, row in latest_observations.iterrows():
        # Prepare inputs exactly like the API
        uo = row['uo'] if pd.notnull(row['uo']) else None
        vo = row['vo'] if pd.notnull(row['vo']) else None
        u10 = row['u10'] if pd.notnull(row['u10']) else None
        v10 = row['v10'] if pd.notnull(row['v10']) else None
        siconc = row['siconc'] if pd.notnull(row['siconc']) else None
        
        req = TrajectoryRequest(
            iceberg_id=row['iceberg_id'],
            timestamp=row['timestamp'].isoformat(),
            latitude=row['latitude'],
            longitude=row['longitude'],
            velocity_ms=row['velocity_ms'] if pd.notnull(row['velocity_ms']) else 0.0,
            heading_deg=row['heading_deg'] if pd.notnull(row['heading_deg']) else 0.0,
            uo=uo,
            vo=vo,
            u10=u10,
            v10=v10,
            siconc=siconc
        )
        
        # 7. Input observations remain unchanged (validate post-predict)
        orig_lat = req.latitude
        orig_lon = req.longitude
        
        seq, meta_row, x_m, y_m = convert_request_to_model_inputs(req)
        predictions = predictor.predict_multi_horizon(seq, meta_row, x_m, y_m)
        
        # 2. Every iceberg receives five horizons
        assert len(predictions) == 5
        total_predictions += 5
        
        has_missing_env = (uo is None or vo is None or u10 is None or v10 is None or siconc is None)
        
        for p in predictions:
            # 4. No prediction contains NaN
            assert not np.isnan(p['predicted_latitude'])
            assert not np.isnan(p['predicted_longitude'])
            assert not np.isnan(p['predicted_dx_m'])
            assert not np.isnan(p['predicted_dy_m'])
            
            # 5. No prediction contains Infinity
            assert not np.isinf(p['predicted_latitude'])
            assert not np.isinf(p['predicted_longitude'])
            assert not np.isinf(p['predicted_dx_m'])
            assert not np.isinf(p['predicted_dy_m'])
            
            # 6. Coordinates remain within valid geographic bounds
            assert -90.0 <= p['predicted_latitude'] <= 90.0
            assert -180.0 <= p['predicted_longitude'] <= 180.0
            
            # 8. Missing environmental values trigger safe fallback for Physics B
            if has_missing_env and req.velocity_ms >= 0.03:
                assert p['selected_model'] == 'persistence_fallback'
                assert p['fallback_used'] == True
                assert p['prediction_quality'] == 'degraded'
            else:
                # 9. Model routing remains consistent with 0.03 m/s policy
                if req.velocity_ms < 0.03:
                    assert p['selected_model'] == 'Persistence'
                elif not has_missing_env:
                    assert p['selected_model'] == 'Physics B'
                    
        # Verify inputs didn't mutate
        assert req.latitude == orig_lat
        assert req.longitude == orig_lon
        
    # 3. Expected maximum output is 550 rows
    assert total_predictions == 550
