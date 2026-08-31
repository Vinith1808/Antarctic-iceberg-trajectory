import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from src.modeling.multi_horizon import MultiHorizonPredictor
from src.modeling.evaluate_baselines import euclidean_error

def assign_horizon_bucket(actual_h):
    if actual_h <= 48:
        return 24
    elif actual_h <= 120:
        return 72
    elif actual_h <= 192:
        return 168
    elif actual_h <= 312:
        return 240
    else:
        return 720

def main():
    print("Evaluating Multi-Horizon Predictor...")
    
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    # We will use MultiHorizonPredictor directly
    mh_predictor = MultiHorizonPredictor() # Wrapper has access to RegimeHybridPredictor
    mh_predictor.predictor.middle_regime_model = 'Persistence'
    
    # Also evaluate pure Persistence and pure Physics B
    mh_persistence = MultiHorizonPredictor()
    mh_persistence.predictor.T_low = 100.0 # Force everything to persistence
    
    mh_physics_b = MultiHorizonPredictor()
    mh_physics_b.predictor.T_high = 0.0 # Force everything to physics
    mh_physics_b.predictor.T_low = 0.0
    mh_physics_b.predictor.middle_regime_model = 'Physics B'
    
    X_test_phys = mh_predictor.predictor.unscale_X(X_test_scaled)
    lats = X_test_phys[:, -1, 0]
    lons = X_test_phys[:, -1, 1]
    vel_ms = X_test_phys[:, -1, 2]
    
    valid_mask = ~np.isnan(lats) & ~np.isnan(lons)
    gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(np.where(valid_mask, lons, 0.0), np.where(valid_mask, lats, 0.0)),
        crs="EPSG:4326"
    )
    gdf_3031 = gdf.to_crs("EPSG:3031")
    x_ms = np.where(valid_mask, gdf_3031.geometry.x, np.nan)
    y_ms = np.where(valid_mask, gdf_3031.geometry.y, np.nan)
    
    predictions = []
    
    # Evaluate every sequence at its EXACT ground truth horizon to prevent temporal mismatch error,
    # then bucket by the requested operational horizons.
    for i in range(len(test_meta)):
        meta_row = test_meta.iloc[i].to_dict()
        meta_row['latitude'] = lats[i]
        meta_row['longitude'] = lons[i]
        
        actual_h = meta_row['target_time_delta_hours']
        
        # Inject the actual horizon to the predictor wrapper
        mh_predictor.horizons = [actual_h]
        mh_persistence.horizons = [actual_h]
        mh_physics_b.horizons = [actual_h]
        
        res_hybrid = mh_predictor.predict_multi_horizon(X_test_phys[i], meta_row, x_ms[i], y_ms[i])[0]
        res_pers = mh_persistence.predict_multi_horizon(X_test_phys[i], meta_row, x_ms[i], y_ms[i])[0]
        res_phys = mh_physics_b.predict_multi_horizon(X_test_phys[i], meta_row, x_ms[i], y_ms[i])[0]
        
        res_hybrid['model_type'] = 'Regime Hybrid'
        res_pers['model_type'] = 'Persistence'
        res_phys['model_type'] = 'Physics B'
        
        for res in [res_hybrid, res_pers, res_phys]:
            res['target_dx_m'] = y_test_raw[i, 0]
            res['target_dy_m'] = y_test_raw[i, 1]
            res['vel_ms'] = vel_ms[i]
            res['bucket'] = assign_horizon_bucket(actual_h)
            predictions.append(res)
        
    df_preds = pd.DataFrame(predictions)
    
    y_raw = np.column_stack([df_preds['target_dx_m'], df_preds['target_dy_m']])
    y_pred = np.column_stack([df_preds['predicted_dx_m'], df_preds['predicted_dy_m']])
    df_preds['EPE_m'] = euclidean_error(y_raw, y_pred)
    df_preds['MAE_x'] = np.abs(df_preds['predicted_dx_m'] - df_preds['target_dx_m'])
    df_preds['MAE_y'] = np.abs(df_preds['predicted_dy_m'] - df_preds['target_dy_m'])
    df_preds['MAE'] = (df_preds['MAE_x'] + df_preds['MAE_y']) / 2.0
    df_preds['SE'] = (df_preds['predicted_dx_m'] - df_preds['target_dx_m'])**2 + (df_preds['predicted_dy_m'] - df_preds['target_dy_m'])**2
    
    analysis = []
    analysis.append("# Phase 9: Multi-Horizon Prediction Evaluation\n")
    
    # 1. Horizon-wise Metrics
    analysis.append("## 1. Horizon-wise Metrics (Regime Hybrid)\n")
    horizon_results = []
    
    df_hybrid = df_preds[df_preds['model_type'] == 'Regime Hybrid']
    
    for bucket in [24, 72, 168, 240, 720]:
        sub_df = df_hybrid[df_hybrid['bucket'] == bucket]
        if len(sub_df) == 0:
            continue
        
        mean_epe = sub_df['EPE_m'].mean()
        med_epe = sub_df['EPE_m'].median()
        p95_epe = sub_df['EPE_m'].quantile(0.95)
        mae = sub_df['MAE'].mean()
        rmse = np.sqrt(sub_df['SE'].mean())
        
        analysis.append(f"### {bucket}h Horizon")
        analysis.append(f"- Sample count: {len(sub_df)}")
        analysis.append(f"- Mean EPE: {mean_epe:.1f} m")
        analysis.append(f"- Median EPE: {med_epe:.1f} m")
        analysis.append(f"- P95 EPE: {p95_epe:.1f} m")
        analysis.append(f"- MAE: {mae:.1f} m")
        analysis.append(f"- RMSE: {rmse:.1f} m\n")
        
    # 2. Kinematic Regime Breakdown (Regime Hybrid)
    analysis.append("## 2. Kinematic Regime Breakdown (Regime Hybrid)\n")
    regimes = {
        'Stationary (<0.01 m/s)': df_hybrid['vel_ms'] < 0.01,
        'Slow-moving (0.01-0.03 m/s)': (df_hybrid['vel_ms'] >= 0.01) & (df_hybrid['vel_ms'] < 0.03),
        'Moving (>=0.03 m/s)': df_hybrid['vel_ms'] >= 0.03
    }
    
    for name, mask in regimes.items():
        sub_df = df_hybrid[mask]
        mean_epe = sub_df['EPE_m'].mean()
        med_epe = sub_df['EPE_m'].median()
        p95_epe = sub_df['EPE_m'].quantile(0.95)
        
        analysis.append(f"### {name}")
        analysis.append(f"- Sample count: {len(sub_df)}")
        analysis.append(f"- Mean EPE: {mean_epe:.1f} m")
        analysis.append(f"- Median EPE: {med_epe:.1f} m")
        analysis.append(f"- P95 EPE: {p95_epe:.1f} m\n")

    # 3. Model Comparison
    analysis.append("## 3. Model Comparison\n")
    
    for bucket in [24, 72, 168, 240, 720]:
        sub_df = df_preds[df_preds['bucket'] == bucket]
        if len(sub_df) == 0:
            continue
        
        analysis.append(f"### {bucket}h Horizon")
        for model in ['Persistence', 'Physics B', 'Regime Hybrid']:
            m_df = sub_df[sub_df['model_type'] == model]
            analysis.append(f"- {model} Mean EPE: {m_df['EPE_m'].mean():.1f} m")
            horizon_results.append({'Horizon_h': bucket, 'Model': model, 'Mean_EPE_m': m_df['EPE_m'].mean()})
        analysis.append("\n")

        
    # PLOTS
    docs_dir = Path('docs')
    figs_dir = docs_dir / 'figures'
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    df_horizons = pd.DataFrame(horizon_results)
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_horizons, x='Horizon_h', y=df_horizons['Mean_EPE_m']/1000.0, hue='Model', marker='o', linewidth=2)
    plt.title('Error Growth vs Prediction Horizon')
    plt.xlabel('Prediction Horizon (hours)')
    plt.ylabel('Mean Endpoint Error (km)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks([24, 72, 168, 240, 720])
    plt.tight_layout()
    plt.savefig(figs_dir / 'horizon_vs_mean_epe.png', dpi=300)
    plt.close()
    
    # Save text
    with open(docs_dir / 'multi_horizon_prediction.md', 'w') as f:
        f.write("\n".join(analysis))

if __name__ == '__main__':
    main()
