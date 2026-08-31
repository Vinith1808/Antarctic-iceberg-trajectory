import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from src.modeling.regime_hybrid import RegimeHybridPredictor
from src.modeling.evaluate_baselines import euclidean_error

def main():
    print("Evaluating Regime-Aware Hybrid Predictor...")
    
    predictor = RegimeHybridPredictor()
    predictor.fit_validation_policy()
    
    # 1. Load Data
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    X_test_phys = predictor.unscale_X(X_test_scaled)
    
    # Pre-calculate x_m, y_m for initial coordinates
    lats = X_test_phys[:, -1, 0]
    lons = X_test_phys[:, -1, 1]
    
    # We must handle NaN coordinates gracefully if they exist.
    # Fortunately, the pipeline forward-filled them, but let's be safe.
    valid_mask = ~np.isnan(lats) & ~np.isnan(lons)
    
    gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            np.where(valid_mask, lons, 0.0), 
            np.where(valid_mask, lats, 0.0)
        ),
        crs="EPSG:4326"
    )
    gdf_3031 = gdf.to_crs("EPSG:3031")
    
    x_ms = np.where(valid_mask, gdf_3031.geometry.x, np.nan)
    y_ms = np.where(valid_mask, gdf_3031.geometry.y, np.nan)
    
    # 2. Predict Trajectories
    predictions = []
    hybrid_dx = []
    hybrid_dy = []
    
    for i in range(len(test_meta)):
        meta_row = test_meta.iloc[i].to_dict()
        # Ensure we provide original lat/lon to meta_row
        meta_row['latitude'] = lats[i]
        meta_row['longitude'] = lons[i]
        
        result = predictor.predict_trajectory(X_test_phys[i], meta_row, x_ms[i], y_ms[i])
        predictions.append(result)
        hybrid_dx.append(result['predicted_dx_m'])
        hybrid_dy.append(result['predicted_dy_m'])
        
    df_preds = pd.DataFrame(predictions)
    y_hybrid = np.column_stack([hybrid_dx, hybrid_dy])
    
    # 3. Calculate Baselines
    # Persistence
    y_pers = np.zeros_like(y_hybrid)
    
    # Physics B
    from src.modeling.physics_baseline import get_physics_features
    iceberg_u, iceberg_v, ocean_u, ocean_v, w_u, w_v, sic, dt = get_physics_features(X_test_phys, test_meta)
    alpha, beta, gamma = predictor.reg_B.coef_
    env_factor = 1.0 - sic
    pred_u = env_factor * (alpha * ocean_u + beta * w_u) + gamma * iceberg_u
    pred_v = env_factor * (alpha * ocean_v + beta * w_v) + gamma * iceberg_v
    
    y_phys_B = np.column_stack([pred_u * dt, pred_v * dt])
    
    # 4. Calculate Metrics
    pers_epe = euclidean_error(y_test_raw, y_pers)
    phys_epe = euclidean_error(y_test_raw, y_phys_B)
    hybrid_epe = euclidean_error(y_test_raw, y_hybrid)
    
    df_preds['persistence_epe'] = pers_epe
    df_preds['physics_b_epe'] = phys_epe
    df_preds['hybrid_epe'] = hybrid_epe
    
    vel_ms = X_test_phys[:, -1, 2]
    
    def get_metrics(epe_arr):
        if len(epe_arr) == 0:
            return {'Mean_EPE_m': np.nan, 'Median_EPE_m': np.nan, 'P95_EPE_m': np.nan}
        return {
            'Mean_EPE_m': np.mean(epe_arr),
            'Median_EPE_m': np.median(epe_arr),
            'P95_EPE_m': np.percentile(epe_arr, 95)
        }
    
    # Kinematic splits
    stat_mask = vel_ms < 0.01
    slow_mask = (vel_ms >= 0.01) & (vel_ms < 0.03)
    move_mask = vel_ms >= 0.03
    
    results_summary = []
    
    models = {
        'Persistence': pers_epe,
        'Physics Model B': phys_epe,
        'Regime Hybrid': hybrid_epe
    }
    
    for m_name, epe in models.items():
        all_m = get_metrics(epe)
        stat_m = get_metrics(epe[stat_mask])
        slow_m = get_metrics(epe[slow_mask])
        move_m = get_metrics(epe[move_mask])
        
        results_summary.append({'Model': m_name, 'Subset': 'All', **all_m})
        results_summary.append({'Model': m_name, 'Subset': 'Stationary (<0.01)', **stat_m})
        results_summary.append({'Model': m_name, 'Subset': 'Slow-moving (0.01-0.03)', **slow_m})
        results_summary.append({'Model': m_name, 'Subset': 'Moving (>=0.03)', **move_m})
        
    df_summary = pd.DataFrame(results_summary)
    
    print("\n--- TEST SET METRICS ---")
    print(df_summary[df_summary['Subset'] == 'All'].to_markdown(index=False, floatfmt=".2f"))
    print("\n--- STATIONARY METRICS ---")
    print(df_summary[df_summary['Subset'] == 'Stationary (<0.01)'].to_markdown(index=False, floatfmt=".2f"))
    print("\n--- SLOW-MOVING METRICS ---")
    print(df_summary[df_summary['Subset'] == 'Slow-moving (0.01-0.03)'].to_markdown(index=False, floatfmt=".2f"))
    print("\n--- MOVING METRICS ---")
    print(df_summary[df_summary['Subset'] == 'Moving (>=0.03)'].to_markdown(index=False, floatfmt=".2f"))
    
    # 5. Model Selection Statistics
    counts = df_preds['selected_model'].value_counts()
    pcts = df_preds['selected_model'].value_counts(normalize=True) * 100
    print("\n--- MODEL SELECTION STATISTICS ---")
    for k, v in counts.items():
        print(f"{k}: {v} ({pcts[k]:.1f}%)")
        
    # 6. Pairwise Comparisons
    mean_hybrid = df_summary[(df_summary['Model'] == 'Regime Hybrid') & (df_summary['Subset'] == 'All')]['Mean_EPE_m'].values[0]
    mean_pers = df_summary[(df_summary['Model'] == 'Persistence') & (df_summary['Subset'] == 'All')]['Mean_EPE_m'].values[0]
    mean_phys = df_summary[(df_summary['Model'] == 'Physics Model B') & (df_summary['Subset'] == 'All')]['Mean_EPE_m'].values[0]
    
    imp_vs_pers = (mean_pers - mean_hybrid) / mean_pers * 100
    imp_vs_phys = (mean_phys - mean_hybrid) / mean_phys * 100
    
    beat_pers = np.mean(hybrid_epe < pers_epe) * 100
    beat_phys = np.mean(hybrid_epe < phys_epe) * 100
    beat_both = np.mean((hybrid_epe < pers_epe) & (hybrid_epe < phys_epe)) * 100
    
    print("\n--- PAIRWISE COMPARISONS ---")
    print(f"Hybrid improvement vs Persistence: {imp_vs_pers:.2f}%")
    print(f"Hybrid improvement vs Physics B: {imp_vs_phys:.2f}%")
    print(f"% Hybrid beats Persistence: {beat_pers:.1f}%")
    print(f"% Hybrid beats Physics B: {beat_phys:.1f}%")
    print(f"% Hybrid beats Both: {beat_both:.1f}%")
    
    # Ensure folder exists
    docs_dir = Path('docs')
    figs_dir = docs_dir / 'figures'
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df_preds.to_csv(docs_dir / 'regime_hybrid_results.csv', index=False)
    
    # 7. Plotting
    plt.figure(figsize=(10, 6))
    
    all_all = df_summary[df_summary['Subset'] == 'All']
    sns.barplot(data=all_all, x='Model', y='Mean_EPE_m', palette='Blues_d')
    plt.ylabel('Mean Endpoint Error (meters)')
    plt.title('Overall Mean EPE: Persistence vs Physics B vs Regime Hybrid')
    for i, v in enumerate(all_all['Mean_EPE_m']):
        plt.text(i, v + 100, f"{v:.0f} m", ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(figs_dir / 'regime_hybrid_comparison.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    main()
