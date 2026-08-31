import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from src.modeling.multi_horizon import MultiHorizonPredictor
from src.visualization.polar_map import create_polar_plot, plot_trajectory_on_ax, wgs84_to_epsg3031

def generate_trajectory_plots():
    docs_dir = Path('docs/figures')
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    mh_predictor = MultiHorizonPredictor()
    mh_predictor.predictor.middle_regime_model = 'Persistence'
    X_test_phys = mh_predictor.predictor.unscale_X(X_test_scaled)
    
    # Specific representative indices we found earlier
    # Stationary: [0, 1, 2, 3, 4]
    # Slow: [18]
    # Moving: [19, 20, 21, 23, 24]
    # d27: [221, 222, 223, 224, 225]
    
    cases = {
        'stationary': 0,
        'slow_moving': 18,
        'moving': 19,
        'outlier_d27': 221
    }
    
    # Collect coordinates for the combined polar map
    all_polar_paths = []
    
    for case_name, idx in cases.items():
        # Get historical coordinates
        hist_lats = X_test_phys[idx, :, 0]
        hist_lons = X_test_phys[idx, :, 1]
        valid_hist = ~np.isnan(hist_lats) & ~np.isnan(hist_lons)
        
        hist_lats = hist_lats[valid_hist]
        hist_lons = hist_lons[valid_hist]
        
        hist_x, hist_y = wgs84_to_epsg3031(hist_lons, hist_lats)
        curr_x, curr_y = hist_x[-1], hist_y[-1]
        
        meta_row = test_meta.iloc[idx].to_dict()
        meta_row['latitude'] = hist_lats[-1]
        meta_row['longitude'] = hist_lons[-1]
        actual_h = meta_row['target_time_delta_hours']
        
        mh_predictor.horizons = [actual_h]
        res = mh_predictor.predict_multi_horizon(X_test_phys[idx], meta_row, curr_x, curr_y)[0]
        
        pred_x, pred_y = wgs84_to_epsg3031([res['predicted_longitude']], [res['predicted_latitude']])
        pred_x = pred_x[0]
        pred_y = pred_y[0]
        
        true_x = curr_x + y_test_raw[idx, 0]
        true_y = curr_y + y_test_raw[idx, 1]
        
        # Save for combined map
        all_polar_paths.append((hist_x, hist_y, curr_x, curr_y, pred_x, pred_y, true_x, true_y, meta_row['iceberg_id']))
        
        # Plot individual case
        fig, ax = create_polar_plot(figsize=(6, 6))
        plot_trajectory_on_ax(ax, hist_x, hist_y, curr_x, curr_y, pred_x, pred_y, true_x, true_y, label_prefix=f"{meta_row['iceberg_id']}")
        
        title = f"Iceberg {meta_row['iceberg_id']} - {case_name.replace('_', ' ').title()}\n"
        title += f"Horizon: {actual_h}h | Model: {res['selected_model']} | Vel: {X_test_phys[idx, -1, 2]:.3f} m/s"
        ax.set_title(title)
        
        plt.tight_layout()
        plt.savefig(docs_dir / f'trajectory_{case_name}.png', dpi=300)
        plt.close()

    # 5. Combined Antarctic Polar Trajectory
    fig, ax = create_polar_plot(figsize=(10, 10))
    for hist_x, hist_y, curr_x, curr_y, pred_x, pred_y, true_x, true_y, ice_id in all_polar_paths:
        plot_trajectory_on_ax(ax, hist_x, hist_y, curr_x, curr_y, pred_x, pred_y, true_x, true_y, label_prefix=ice_id)
    ax.set_title("Antarctic Polar Trajectories - Representative Cases")
    plt.tight_layout()
    plt.savefig(docs_dir / 'antarctic_polar_trajectory.png', dpi=300)
    plt.close()
    
    # 6. Multi-Horizon Forecast Visualization
    # Let's use the moving iceberg (idx 19) to show 5 horizons cleanly
    idx = 19
    meta_row = test_meta.iloc[idx].to_dict()
    hist_lats = X_test_phys[idx, :, 0]
    hist_lons = X_test_phys[idx, :, 1]
    valid_hist = ~np.isnan(hist_lats) & ~np.isnan(hist_lons)
    hist_x, hist_y = wgs84_to_epsg3031(hist_lons[valid_hist], hist_lats[valid_hist])
    curr_x, curr_y = hist_x[-1], hist_y[-1]
    meta_row['latitude'] = hist_lats[valid_hist][-1]
    meta_row['longitude'] = hist_lons[valid_hist][-1]
    
    mh_predictor.horizons = [24.0, 72.0, 168.0, 240.0, 720.0]
    res_multi = mh_predictor.predict_multi_horizon(X_test_phys[idx], meta_row, curr_x, curr_y)
    
    fig, ax = create_polar_plot(figsize=(7, 7))
    ax.plot(hist_x, hist_y, color='gray', linestyle='-', marker='.', alpha=0.6, label='Historical Path')
    ax.plot(curr_x, curr_y, color='black', marker='s', markersize=8, label='Current Location')
    
    colors = ['yellow', 'orange', 'red', 'purple', 'darkred']
    for i, r in enumerate(res_multi):
        px, py = wgs84_to_epsg3031([r['predicted_longitude']], [r['predicted_latitude']])
        ax.plot([curr_x, px[0]], [curr_y, py[0]], color=colors[i], linestyle='--', marker='X', markersize=8, label=f"{r['horizon_hours']}h Forecast")
    
    ax.set_title(f"Multi-Horizon Forecast - Iceberg {meta_row['iceberg_id']}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(docs_dir / 'multi_horizon_forecast.png', dpi=300)
    plt.close()
    
    # 7. Model Trajectory Comparison
    # Let's compare Persistence, Physics B, and Hybrid on idx 19
    mh_persistence = MultiHorizonPredictor(horizons=[168.0])
    mh_persistence.predictor.T_low = 100.0
    
    mh_physics_b = MultiHorizonPredictor(horizons=[168.0])
    mh_physics_b.predictor.T_high = 0.0
    mh_physics_b.predictor.T_low = 0.0
    mh_physics_b.predictor.middle_regime_model = 'Physics B'
    
    mh_hybrid = MultiHorizonPredictor(horizons=[168.0])
    mh_hybrid.predictor.middle_regime_model = 'Persistence'
    
    res_pers = mh_persistence.predict_multi_horizon(X_test_phys[idx], meta_row, curr_x, curr_y)[0]
    res_phys = mh_physics_b.predict_multi_horizon(X_test_phys[idx], meta_row, curr_x, curr_y)[0]
    res_hybr = mh_hybrid.predict_multi_horizon(X_test_phys[idx], meta_row, curr_x, curr_y)[0]
    
    fig, ax = create_polar_plot(figsize=(7, 7))
    ax.plot(hist_x, hist_y, color='gray', linestyle='-', marker='.', alpha=0.6, label='Historical Path')
    ax.plot(curr_x, curr_y, color='black', marker='s', markersize=8, label='Current Location')
    
    true_x = curr_x + y_test_raw[idx, 0]
    true_y = curr_y + y_test_raw[idx, 1]
    
    for r, name, col in zip([res_pers, res_phys, res_hybr], ['Persistence', 'Physics B', 'Regime Hybrid'], ['blue', 'orange', 'red']):
        px, py = wgs84_to_epsg3031([r['predicted_longitude']], [r['predicted_latitude']])
        ax.plot([curr_x, px[0]], [curr_y, py[0]], color=col, linestyle='--', marker='X', markersize=8, label=f"{name}")
        
    ax.plot([curr_x, true_x], [curr_y, true_y], color='green', linestyle='-', marker='*', markersize=10, label="Ground Truth (168h)")
    ax.set_title(f"Model Comparison - Iceberg {meta_row['iceberg_id']} (168h)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(docs_dir / 'model_trajectory_comparison.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    generate_trajectory_plots()
