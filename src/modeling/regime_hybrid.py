import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import joblib

from src.modeling.physics_baseline import fit_physics_models, get_physics_features
from src.modeling.evaluate_baselines import euclidean_error

class RegimeHybridPredictor:
    def __init__(self):
        print("Initializing Regime Hybrid Predictor...")
        self.reg_A, self.reg_B, self.unscale_X = fit_physics_models()
        self.T_low = 0.01
        self.T_high = 0.03
        self.middle_regime_model = 'Physics B' # Default, will be updated via validation
        
    def fit_validation_policy(self):
        """
        Evaluate the intermediate regime (0.01 <= v < 0.03) on the validation set
        to determine the optimal policy.
        """
        val_data = np.load('data/processed/sequences/validation.npz')
        X_val_scaled = np.nan_to_num(val_data['X'], nan=0.0)
        y_val_raw = np.nan_to_num(val_data['y'], nan=0.0)
        val_meta = pd.read_parquet('data/processed/sequences/validation_meta.parquet')
        
        X_val_phys = self.unscale_X(X_val_scaled)
        iceberg_u, iceberg_v, ocean_u, ocean_v, w_u, w_v, sic_feat, delta_t_s = get_physics_features(X_val_phys, val_meta)
        
        vel_ms = X_val_phys[:, -1, 2]
        
        # Intermediate mask
        mid_mask = (vel_ms >= self.T_low) & (vel_ms < self.T_high)
        
        if np.sum(mid_mask) == 0:
            print("No validation samples in the intermediate regime. Defaulting to Physics B.")
            self.middle_regime_model = 'Physics B'
            return
            
        y_val_mid = y_val_raw[mid_mask]
        
        # Persistence for middle regime
        pers_mid = np.zeros_like(y_val_mid)
        pers_epe = np.mean(euclidean_error(y_val_mid, pers_mid))
        
        # Physics B for middle regime
        alpha, beta, gamma = self.reg_B.coef_
        env_factor = 1.0 - sic_feat[mid_mask]
        pred_u = env_factor * (alpha * ocean_u[mid_mask] + beta * w_u[mid_mask]) + gamma * iceberg_u[mid_mask]
        pred_v = env_factor * (alpha * ocean_v[mid_mask] + beta * w_v[mid_mask]) + gamma * iceberg_v[mid_mask]
        
        phys_mid = np.column_stack([pred_u * delta_t_s[mid_mask], pred_v * delta_t_s[mid_mask]])
        phys_epe = np.mean(euclidean_error(y_val_mid, phys_mid))
        
        print(f"\n--- VALIDATION POLICY SELECTION (0.01 <= v < 0.03) ---")
        print(f"Validation Samples in Regime: {np.sum(mid_mask)}")
        print(f"Persistence Mean EPE: {pers_epe:.2f} m")
        print(f"Physics B Mean EPE: {phys_epe:.2f} m")
        
        if pers_epe < phys_epe:
            self.middle_regime_model = 'Persistence'
            print("Selected Model for Middle Regime: Persistence")
        else:
            self.middle_regime_model = 'Physics B'
            print("Selected Model for Middle Regime: Physics B")

    def predict_trajectory(self, sequence_X_phys, meta_row, x_m, y_m):
        """
        Predicts trajectory for a single sequence.
        sequence_X_phys: [10, 22] physical features
        meta_row: dict or Series containing target_time_delta_hours, iceberg_id, target_timestamp, etc.
        x_m, y_m: initial EPSG:3031 coordinates
        """
        vel_ms = sequence_X_phys[-1, 2]
        delta_t_s = meta_row['target_time_delta_hours'] * 3600.0
        
        selected_model = None
        regime = None
        pred_dx = 0.0
        pred_dy = 0.0
        
        # Edge cases: missing velocity or delta_t <= 0
        if not np.isfinite(vel_ms) or delta_t_s <= 0:
            selected_model = 'persistence_fallback'
            regime = 'edge_case'
            
        else:
            if vel_ms < self.T_low:
                regime = 'Stationary'
                selected_model = 'Persistence'
            elif vel_ms >= self.T_high:
                regime = 'Moving'
                selected_model = 'Physics B'
            else:
                regime = 'Slow-moving'
                selected_model = self.middle_regime_model
                
            if selected_model == 'Physics B':
                # Ensure we handle potentially missing environmental data properly
                X_batch = sequence_X_phys[np.newaxis, :, :]
                meta_batch = pd.DataFrame([meta_row])
                
                i_u, i_v, o_u, o_v, w_u, w_v, sic, dt = get_physics_features(X_batch, meta_batch)
                
                # Check if ANY required variable is non-finite
                if not (np.isfinite(i_u[0]) and np.isfinite(i_v[0]) and 
                        np.isfinite(o_u[0]) and np.isfinite(o_v[0]) and 
                        np.isfinite(w_u[0]) and np.isfinite(w_v[0]) and 
                        np.isfinite(sic[0])):
                    selected_model = 'persistence_fallback'
                    regime = 'edge_case'
                else:
                    alpha, beta, gamma = self.reg_B.coef_
                    env_factor = 1.0 - sic[0]
                    pred_u = env_factor * (alpha * o_u[0] + beta * w_u[0]) + gamma * i_u[0]
                    pred_v = env_factor * (alpha * o_v[0] + beta * w_v[0]) + gamma * i_v[0]
                    
                    pred_dx = pred_u * dt[0]
                    pred_dy = pred_v * dt[0]
                    
                    # Final safety check on Physics B displacement
                    if not (np.isfinite(pred_dx) and np.isfinite(pred_dy)):
                        selected_model = 'persistence_fallback'
                        regime = 'edge_case'

        if selected_model in ['Persistence', 'persistence_fallback']:
            pred_dx = 0.0
            pred_dy = 0.0
            pred_lat = meta_row.get('latitude', np.nan)
            pred_lon = meta_row.get('longitude', np.nan)
        else:
            # Add displacement to initial coordinates
            pred_x_m = x_m + pred_dx
            pred_y_m = y_m + pred_dy
            
            # Convert to EPSG:4326 (lat/lon)
            if not np.isfinite(pred_x_m) or not np.isfinite(pred_y_m):
                selected_model = 'persistence_fallback'
                regime = 'edge_case'
                pred_dx = 0.0
                pred_dy = 0.0
                pred_lat = meta_row.get('latitude', np.nan)
                pred_lon = meta_row.get('longitude', np.nan)
            else:
                gdf = gpd.GeoDataFrame(geometry=[Point(pred_x_m, pred_y_m)], crs="EPSG:3031")
                gdf_wgs = gdf.to_crs("EPSG:4326")
                
                pred_lon = gdf_wgs.geometry.x[0]
                pred_lat = gdf_wgs.geometry.y[0]
                
                if not (np.isfinite(pred_lat) and np.isfinite(pred_lon)):
                    selected_model = 'persistence_fallback'
                    regime = 'edge_case'
                    pred_dx = 0.0
                    pred_dy = 0.0
                    pred_lat = meta_row.get('latitude', np.nan)
                    pred_lon = meta_row.get('longitude', np.nan)
        
        return {
            'iceberg_id': meta_row.get('iceberg_id', 'unknown'),
            'timestamp': meta_row.get('target_timestamp', pd.NaT),
            'original_latitude': meta_row.get('latitude', np.nan),
            'original_longitude': meta_row.get('longitude', np.nan),
            'predicted_dx_m': pred_dx,
            'predicted_dy_m': pred_dy,
            'predicted_latitude': pred_lat,
            'predicted_longitude': pred_lon,
            'regime': regime,
            'selected_model': selected_model,
            'prediction_horizon_hours': meta_row['target_time_delta_hours']
        }
