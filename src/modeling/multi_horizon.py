import pandas as pd
from typing import List, Dict, Any
from src.modeling.regime_hybrid import RegimeHybridPredictor

class MultiHorizonPredictor:
    """
    Lightweight multi-horizon inference wrapper around RegimeHybridPredictor.
    Generates trajectory predictions for multiple operational forecast horizons.
    """
    def __init__(self, predictor=None, horizons=[24.0, 72.0, 168.0, 240.0, 720.0]):
        self.predictor = predictor if predictor else RegimeHybridPredictor()
        self.horizons = horizons
        
    def predict_multi_horizon(self, sequence_X_phys, meta_row, x_m, y_m) -> List[Dict[str, Any]]:
        """
        Generates predictions for all configured horizons.
        """
        results = []
        for h in self.horizons:
            # Create a copy of meta_row to inject target horizon safely
            h_meta = meta_row.copy()
            if isinstance(h_meta, pd.Series):
                h_meta = h_meta.to_dict()
                
            h_meta['target_time_delta_hours'] = float(h)
            
            # Predict single horizon using the underlying safe predictor
            res = self.predictor.predict_trajectory(sequence_X_phys, h_meta, x_m, y_m)
            
            is_fallback = 'fallback' in res['selected_model']
            
            results.append({
                'iceberg_id': res['iceberg_id'],
                'initial_timestamp': meta_row.get('timestamp', pd.NaT),
                'horizon_hours': float(h),
                'predicted_dx_m': res['predicted_dx_m'],
                'predicted_dy_m': res['predicted_dy_m'],
                'predicted_latitude': res['predicted_latitude'],
                'predicted_longitude': res['predicted_longitude'],
                'selected_model': res['selected_model'],
                'prediction_quality': 'degraded' if is_fallback else 'nominal',
                'fallback_used': is_fallback
            })
            
        return results
