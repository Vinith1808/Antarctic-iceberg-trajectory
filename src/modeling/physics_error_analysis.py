import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr

from src.modeling.physics_baseline import fit_physics_models, get_physics_features
from src.modeling.evaluate_baselines import euclidean_error

def main():
    print("Running Physics Baseline Error & Regime Analysis...")
    
    # 1. Load Data
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    # 2. Get Physics Models & Unscale X
    _, reg_B, unscale_X = fit_physics_models()
    X_test_phys = unscale_X(X_test_scaled)
    
    # Extract features for last sequence step
    last_obs = X_test_phys[:, -1, :]
    lat = last_obs[:, 0]
    lon = last_obs[:, 1]
    vel_ms = last_obs[:, 2]
    heading_deg = last_obs[:, 3]
    distance_m = last_obs[:, 4]
    uo = last_obs[:, 5]
    vo = last_obs[:, 6]
    curr_speed = last_obs[:, 7]
    u10 = last_obs[:, 9]
    v10 = last_obs[:, 10]
    wind_speed = last_obs[:, 11]
    siconc = np.clip(last_obs[:, 13], 0.0, 1.0)
    
    curr_avail = last_obs[:, 19]
    wind_avail = last_obs[:, 20]
    ice_avail = last_obs[:, 21]
    
    siconc = np.where(ice_avail == 1, siconc, 0.0)
    
    # 3. Calculate Predictions
    iceberg_u, iceberg_v, ocean_u, ocean_v, w_u, w_v, sic_feat, delta_t_s = get_physics_features(X_test_phys, test_meta)
    
    # Physics B
    alpha, beta, gamma = reg_B.coef_
    env_factor = 1.0 - sic_feat
    pred_u_B = env_factor * (alpha * ocean_u + beta * w_u) + gamma * iceberg_u
    pred_v_B = env_factor * (alpha * ocean_v + beta * w_v) + gamma * iceberg_v
    phys_dx = pred_u_B * delta_t_s
    phys_dy = pred_v_B * delta_t_s
    y_phys_B = np.column_stack([phys_dx, phys_dy])
    
    # Persistence
    N = len(y_test_raw)
    y_pers = np.zeros((N, 2))
    
    # CV
    cv_dx = iceberg_u * delta_t_s
    cv_dy = iceberg_v * delta_t_s
    y_cv = np.column_stack([cv_dx, cv_dy])
    
    actual_dx = y_test_raw[:, 0]
    actual_dy = y_test_raw[:, 1]
    
    # 4. Errors
    phys_epe = euclidean_error(y_test_raw, y_phys_B)
    pers_epe = euclidean_error(y_test_raw, y_pers)
    cv_epe = euclidean_error(y_test_raw, y_cv)
    
    phys_err_x = phys_dx - actual_dx
    phys_err_y = phys_dy - actual_dy
    
    phys_err_speed = np.zeros_like(phys_epe)
    valid_t = delta_t_s > 0
    phys_err_speed[valid_t] = phys_epe[valid_t] / delta_t_s[valid_t]
    
    # 5. Construct Diagnostic Dataset
    df = test_meta.copy()
    df['initial_latitude'] = lat
    df['initial_longitude'] = lon
    df['initial_velocity_ms'] = vel_ms
    df['initial_heading_deg'] = heading_deg
    df['distance_travelled_prev_m'] = distance_m
    df['physics_dx'] = phys_dx
    df['physics_dy'] = phys_dy
    df['actual_dx'] = actual_dx
    df['actual_dy'] = actual_dy
    df['physics_epe'] = phys_epe
    df['persistence_epe'] = pers_epe
    df['constant_velocity_epe'] = cv_epe
    df['sea_ice_concentration'] = siconc
    df['current_speed'] = curr_speed
    df['wind_speed'] = wind_speed
    df['current_available'] = curr_avail
    df['wind_available'] = wind_avail
    df['seaice_available'] = ice_avail
    df['physics_error_x'] = phys_err_x
    df['physics_error_y'] = phys_err_y
    df['physics_error_speed'] = phys_err_speed
    
    # 6. Prediction Bias
    df['actual_displacement_magnitude'] = np.sqrt(actual_dx**2 + actual_dy**2)
    df['predicted_displacement_magnitude'] = np.sqrt(phys_dx**2 + phys_dy**2)
    df['prediction_minus_actual'] = df['predicted_displacement_magnitude'] - df['actual_displacement_magnitude']
    
    # Save Diagnostic File
    docs_dir = Path('docs')
    docs_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(docs_dir / 'physics_error_analysis.csv', index=False)
    
    # --- ANALYSIS ---
    analysis_text = ["# Phase 8.7.1: Physics Baseline Error & Regime Analysis\n"]
    
    # 3. Error Correlation Analysis
    analysis_text.append("## 1. Error Correlation Analysis (Spearman Rank)")
    corrs = {
        'Initial Iceberg Speed': spearmanr(df['physics_epe'], df['initial_velocity_ms'])[0],
        'Target Time Horizon': spearmanr(df['physics_epe'], df['target_time_delta_hours'])[0],
        'Ocean Current Speed': spearmanr(df['physics_epe'], df['current_speed'])[0],
        'Wind Speed': spearmanr(df['physics_epe'], df['wind_speed'])[0],
        'Sea-Ice Concentration': spearmanr(df['physics_epe'], df['sea_ice_concentration'])[0],
        'Absolute Latitude': spearmanr(df['physics_epe'], np.abs(df['initial_latitude']))[0],
        'Previous Distance Travelled': spearmanr(df['physics_epe'], df['distance_travelled_prev_m'])[0]
    }
    for k, v in corrs.items():
        analysis_text.append(f"* **{k}**: {v:.3f}")
    analysis_text.append("\n*Note: These are descriptive test-set correlations intended to identify failure modes, NOT to tune future models.*")
    
    # 4. Regime Analysis
    analysis_text.append("\n## 2. Regime Analysis")
    
    def calc_regime(df_sub, name):
        if len(df_sub) == 0:
            return ""
        return f"| {name} | {len(df_sub)} | {df_sub['physics_epe'].mean():.1f} | {df_sub['physics_epe'].median():.1f} | {np.percentile(df_sub['physics_epe'], 90):.1f} | {np.percentile(df_sub['physics_epe'], 95):.1f} | {df_sub['predicted_displacement_magnitude'].mean():.1f} | {df_sub['actual_displacement_magnitude'].mean():.1f} |"

    analysis_text.append("| Regime | Count | Mean EPE (m) | Median EPE (m) | P90 EPE (m) | P95 EPE (m) | Mean Pred Disp (m) | Mean Actual Disp (m) |")
    analysis_text.append("|---|---|---|---|---|---|---|---|")
    analysis_text.append(calc_regime(df[df['initial_velocity_ms'] < 0.01], "Stationary (<0.01 m/s)"))
    analysis_text.append(calc_regime(df[df['initial_velocity_ms'] >= 0.01], "Moving (>=0.01 m/s)"))
    
    analysis_text.append("\n### Moving Velocity Bins:")
    analysis_text.append("| Regime | Count | Mean EPE (m) | Median EPE (m) | P90 EPE (m) | P95 EPE (m) | Mean Pred Disp (m) | Mean Actual Disp (m) |")
    analysis_text.append("|---|---|---|---|---|---|---|---|")
    analysis_text.append(calc_regime(df[(df['initial_velocity_ms'] >= 0.01) & (df['initial_velocity_ms'] < 0.03)], "0.01 - 0.03 m/s"))
    analysis_text.append(calc_regime(df[(df['initial_velocity_ms'] >= 0.03) & (df['initial_velocity_ms'] < 0.10)], "0.03 - 0.10 m/s"))
    analysis_text.append(calc_regime(df[(df['initial_velocity_ms'] >= 0.10) & (df['initial_velocity_ms'] < 0.30)], "0.10 - 0.30 m/s"))
    analysis_text.append(calc_regime(df[df['initial_velocity_ms'] >= 0.30], "> 0.30 m/s"))
    
    # 5. Sea-Ice Analysis
    analysis_text.append("\n## 3. Sea-Ice Analysis (Physics Model B)")
    analysis_text.append("| SIC Regime | Count | Mean EPE (m) | Median EPE (m) |")
    analysis_text.append("|---|---|---|---|")
    def calc_sic(df_sub, name):
        if len(df_sub) == 0: return ""
        return f"| {name} | {len(df_sub)} | {df_sub['physics_epe'].mean():.1f} | {df_sub['physics_epe'].median():.1f} |"
    analysis_text.append(calc_sic(df[df['sea_ice_concentration'] < 0.2], "SIC < 0.2"))
    analysis_text.append(calc_sic(df[(df['sea_ice_concentration'] >= 0.2) & (df['sea_ice_concentration'] < 0.5)], "0.2 - 0.5"))
    analysis_text.append(calc_sic(df[(df['sea_ice_concentration'] >= 0.5) & (df['sea_ice_concentration'] < 0.8)], "0.5 - 0.8"))
    analysis_text.append(calc_sic(df[df['sea_ice_concentration'] >= 0.8], "SIC >= 0.8"))
    
    # 6. Prediction Bias Analysis
    analysis_text.append("\n## 4. Prediction Bias Analysis")
    analysis_text.append(f"* **Overall Mean Bias**: {df['prediction_minus_actual'].mean():.1f} m (Positive = Overprediction)")
    analysis_text.append(f"* **Overall Median Bias**: {df['prediction_minus_actual'].median():.1f} m")
    
    df_stat = df[df['initial_velocity_ms'] < 0.01]
    analysis_text.append(f"* **Stationary Mean Bias**: {df_stat['prediction_minus_actual'].mean():.1f} m")
    analysis_text.append(f"* **Stationary Median Bias**: {df_stat['prediction_minus_actual'].median():.1f} m")
    
    df_mov = df[df['initial_velocity_ms'] >= 0.01]
    analysis_text.append(f"* **Moving Mean Bias**: {df_mov['prediction_minus_actual'].mean():.1f} m")
    analysis_text.append(f"* **Moving Median Bias**: {df_mov['prediction_minus_actual'].median():.1f} m")
    
    # 7. Outlier Analysis
    analysis_text.append("\n## 5. Outlier Analysis (Top 20 Errors)")
    top_20 = df.nlargest(20, 'physics_epe')
    analysis_text.append("| Iceberg | Target | EPE (km) | Actual Disp (km) | Pred Disp (km) | Init Vel (m/s) | Curr Speed (m/s) | Wind (m/s) | SIC | Horizon (h) |")
    analysis_text.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, row in top_20.iterrows():
        analysis_text.append(f"| {row['iceberg_id']} | {row['target_timestamp'].strftime('%Y-%m-%d')} | {row['physics_epe']/1000:.1f} | {row['actual_displacement_magnitude']/1000:.1f} | {row['predicted_displacement_magnitude']/1000:.1f} | {row['initial_velocity_ms']:.2f} | {row['current_speed']:.2f} | {row['wind_speed']:.1f} | {row['sea_ice_concentration']:.2f} | {row['target_time_delta_hours']} |")
    
    # 8. Physics vs Persistence
    df['physics_wins'] = df['physics_epe'] < df['persistence_epe']
    analysis_text.append("\n## 6. Physics vs Persistence Crossover")
    bins = [0, 0.01, 0.03, 0.10, 0.30, 2.0]
    labels = ['<0.01', '0.01-0.03', '0.03-0.10', '0.10-0.30', '>0.30']
    df['vel_bin'] = pd.cut(df['initial_velocity_ms'], bins=bins, labels=labels, right=False)
    cross_df = df.groupby('vel_bin', observed=False)['physics_wins'].mean() * 100
    
    analysis_text.append("| Velocity Bin (m/s) | % where Physics B beats Persistence |")
    analysis_text.append("|---|---|")
    for b, v in cross_df.items():
        analysis_text.append(f"| {b} | {v:.1f}% |")
        
    # Generate MD
    with open('docs/physics_error_analysis.md', 'w') as f:
        f.write("\n".join(analysis_text))
        
    # --- PLOTTING ---
    figs_dir = Path('docs/figures')
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Error vs Velocity
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x='initial_velocity_ms', y=df['physics_epe']/1000, alpha=0.6)
    plt.xlabel('Initial Iceberg Velocity (m/s)')
    plt.ylabel('Physics B EPE (km)')
    plt.title('Physics Error vs Initial Iceberg Velocity')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figs_dir / 'error_vs_velocity.png', dpi=300)
    plt.close()
    
    # 2. Error vs Horizon
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x='target_time_delta_hours', y=df['physics_epe']/1000)
    plt.xlabel('Target Horizon (hours)')
    plt.ylabel('Physics B EPE (km)')
    plt.title('Physics Error vs Target Horizon')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figs_dir / 'error_vs_horizon.png', dpi=300)
    plt.close()
    
    # 3. Error vs SIC
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x='sea_ice_concentration', y=df['physics_epe']/1000, alpha=0.6)
    plt.xlabel('Sea-Ice Concentration')
    plt.ylabel('Physics B EPE (km)')
    plt.title('Physics Error vs Sea-Ice Concentration')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figs_dir / 'error_vs_sic.png', dpi=300)
    plt.close()
    
    # 4. Predicted vs Actual Mag
    plt.figure(figsize=(6, 6))
    max_val = max(df['actual_displacement_magnitude'].max(), df['predicted_displacement_magnitude'].max()) / 1000
    sns.scatterplot(data=df, x=df['actual_displacement_magnitude']/1000, y=df['predicted_displacement_magnitude']/1000, alpha=0.5)
    plt.plot([0, max_val], [0, max_val], 'r--')
    plt.xlabel('Actual Displacement (km)')
    plt.ylabel('Predicted Displacement (km)')
    plt.title('Physics B Predicted vs Actual Displacement Magnitude')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figs_dir / 'predicted_vs_actual.png', dpi=300)
    plt.close()
    
    # 5. Physics vs Persistence
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x=df['persistence_epe']/1000, y=df['physics_epe']/1000, hue='initial_velocity_ms', palette='viridis', alpha=0.7)
    max_epe = max(df['persistence_epe'].max(), df['physics_epe'].max()) / 1000
    plt.plot([0, max_epe], [0, max_epe], 'r--', label='Equal Performance')
    plt.xlabel('Persistence EPE (km)')
    plt.ylabel('Physics B EPE (km)')
    plt.title('Physics vs Persistence Error per Sequence')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figs_dir / 'physics_vs_persistence.png', dpi=300)
    plt.close()
    
    # 6. Error dist by regime
    plt.figure(figsize=(10, 6))
    df['Regime'] = np.where(df['initial_velocity_ms'] < 0.01, 'Stationary', 'Moving')
    sns.kdeplot(data=df, x=df['physics_epe']/1000, hue='Regime', fill=True, common_norm=False, alpha=0.4)
    plt.xlabel('Physics B EPE (km)')
    plt.title('Physics B Error Distribution by Kinematic Regime')
    plt.xlim(0, 300)
    plt.tight_layout()
    plt.savefig(figs_dir / 'error_distribution_regimes.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    main()
