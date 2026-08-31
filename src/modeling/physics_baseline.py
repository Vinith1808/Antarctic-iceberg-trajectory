import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import torch

from src.modeling.lstm import BaselineLSTM
from src.modeling.evaluate_baselines import euclidean_error

def get_physics_features(X, meta):
    """
    Extract physics features from the LAST observation of each sequence.
    X shape: (N, 10, 22)
    meta: DataFrame of sequence metadata
    """
    # 2=velocity_ms, 3=heading_deg, 5=uo, 6=vo, 9=u10, 10=v10, 13=siconc
    # 19=current_available, 20=wind_available, 21=seaice_available
    
    last_obs = X[:, -1, :]
    
    vel_ms = last_obs[:, 2]
    heading_deg = last_obs[:, 3]
    
    iceberg_u = vel_ms * np.sin(np.radians(heading_deg))
    iceberg_v = vel_ms * np.cos(np.radians(heading_deg))
    
    # Handle NaNs if any (e.g., zero movement)
    iceberg_u = np.nan_to_num(iceberg_u, nan=0.0)
    iceberg_v = np.nan_to_num(iceberg_v, nan=0.0)
    
    uo = last_obs[:, 5]
    vo = last_obs[:, 6]
    curr_avail = last_obs[:, 19]
    ocean_u = np.where(curr_avail == 1, uo, 0.0)
    ocean_v = np.where(curr_avail == 1, vo, 0.0)
    
    u10 = last_obs[:, 9]
    v10 = last_obs[:, 10]
    wind_avail = last_obs[:, 20]
    wind_u = np.where(wind_avail == 1, u10, 0.0)
    wind_v = np.where(wind_avail == 1, v10, 0.0)
    
    siconc = last_obs[:, 13]
    ice_avail = last_obs[:, 21]
    siconc = np.clip(siconc, 0.0, 1.0)
    siconc = np.where(ice_avail == 1, siconc, 0.0)
    
    delta_t_s = meta['target_time_delta_hours'].values * 3600.0
    
    return iceberg_u, iceberg_v, ocean_u, ocean_v, wind_u, wind_v, siconc, delta_t_s

def build_regression_dataset_A(ocean_u, ocean_v, wind_u, wind_v, iceberg_u, iceberg_v, target_u, target_v):
    # Equation: V = alpha*ocean + beta*wind + gamma*iceberg
    X_u = np.column_stack([ocean_u, wind_u, iceberg_u])
    X_v = np.column_stack([ocean_v, wind_v, iceberg_v])
    
    X_reg = np.vstack([X_u, X_v])
    y_reg = np.concatenate([target_u, target_v])
    
    return X_reg, y_reg

def build_regression_dataset_B(ocean_u, ocean_v, wind_u, wind_v, iceberg_u, iceberg_v, siconc, target_u, target_v):
    env_factor = 1.0 - siconc
    
    X_u = np.column_stack([env_factor * ocean_u, env_factor * wind_u, iceberg_u])
    X_v = np.column_stack([env_factor * ocean_v, env_factor * wind_v, iceberg_v])
    
    X_reg = np.vstack([X_u, X_v])
    y_reg = np.concatenate([target_u, target_v])
    
    return X_reg, y_reg

def fit_physics_models():
    # 1. Load Train Data for fitting
    train_data = np.load('data/processed/sequences/train.npz')
    # Unscaled raw targets
    y_train = np.nan_to_num(train_data['y'], nan=0.0)
    train_meta = pd.read_parquet('data/processed/sequences/train_meta.parquet')
    
    # Need to load X unscaled for environmental variables? 
    # WAIT! X in train.npz is SCALED!
    # If X is scaled, then uo, vo, u10, v10, etc., are standardized! 
    # Physics vectors require true physical units (m/s).
    # We must INVERSE TRANSFORM X_train to recover physical vectors!
    
    scaler = joblib.load('models/preprocessing/scaler.pkl')
    # Let's cleanly inverse-transform the entire X tensor to physical units.
    def unscale_X(X_arr):
        N, T, F = X_arr.shape
        X_2d = X_arr.reshape(-1, F)
        
        # We need the scale_features_idx used during training.
        features = [
            'latitude', 'longitude', 'velocity_ms', 'heading_deg', 'distance_m',
            'uo', 'vo', 'current_speed_ms', 'current_direction_deg',
            'u10', 'v10', 'wind_speed_ms', 'wind_direction_deg',
            'siconc', 'time_since_previous_observation_hours',
            'month_sin', 'month_cos', 'day_of_year_sin', 'day_of_year_cos',
            'current_available', 'wind_available', 'seaice_available'
        ]
        scale_features_idx = [i for i, f in enumerate(features) if f not in [
            'current_available', 'wind_available', 'seaice_available',
            'month_sin', 'month_cos', 'day_of_year_sin', 'day_of_year_cos'
        ]]
        
        X_unscaled_2d = X_2d.copy()
        X_unscaled_2d[:, scale_features_idx] = scaler.inverse_transform(X_2d[:, scale_features_idx])
        return X_unscaled_2d.reshape(N, T, F)
    
    X_train_phys = unscale_X(np.nan_to_num(train_data['X'], nan=0.0))
    
    iceberg_u, iceberg_v, ocean_u, ocean_v, wind_u, wind_v, siconc, delta_t_s = get_physics_features(X_train_phys, train_meta)
    
    target_dx = y_train[:, 0]
    target_dy = y_train[:, 1]
    
    # Filter valid times (time > 0)
    valid = delta_t_s > 0
    target_u = np.zeros_like(target_dx)
    target_v = np.zeros_like(target_dy)
    target_u[valid] = target_dx[valid] / delta_t_s[valid]
    target_v[valid] = target_dy[valid] / delta_t_s[valid]
    
    # Fit Model A
    X_reg_A, y_reg_A = build_regression_dataset_A(
        ocean_u[valid], ocean_v[valid], 
        wind_u[valid], wind_v[valid], 
        iceberg_u[valid], iceberg_v[valid], 
        target_u[valid], target_v[valid]
    )
    reg_A = LinearRegression(fit_intercept=False).fit(X_reg_A, y_reg_A)
    params_A = reg_A.coef_
    
    # Fit Model B
    X_reg_B, y_reg_B = build_regression_dataset_B(
        ocean_u[valid], ocean_v[valid], 
        wind_u[valid], wind_v[valid], 
        iceberg_u[valid], iceberg_v[valid], 
        siconc[valid], target_u[valid], target_v[valid]
    )
    reg_B = LinearRegression(fit_intercept=False).fit(X_reg_B, y_reg_B)
    params_B = reg_B.coef_
    
    print("--- FITTED PARAMETERS (TRAIN SET) ---")
    print(f"Model A: alpha (ocean)={params_A[0]:.4f}, beta (wind)={params_A[1]:.4f}, gamma (iceberg)={params_A[2]:.4f}")
    print(f"Model B: alpha (ocean)={params_B[0]:.4f}, beta (wind)={params_B[1]:.4f}, gamma (iceberg)={params_B[2]:.4f}")
    
    return reg_A, reg_B, unscale_X

def evaluate_on_test(reg_A, reg_B, unscale_X):
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    X_test_phys = unscale_X(X_test_scaled)
    
    iceberg_u, iceberg_v, ocean_u, ocean_v, wind_u, wind_v, siconc, delta_t_s = get_physics_features(X_test_phys, test_meta)
    
    N = len(y_test_raw)
    
    # Persistence
    pers_dx = np.zeros(N)
    pers_dy = np.zeros(N)
    y_pers = np.column_stack([pers_dx, pers_dy])
    
    # Constant Velocity
    cv_dx = iceberg_u * delta_t_s
    cv_dy = iceberg_v * delta_t_s
    y_cv = np.column_stack([cv_dx, cv_dy])
    
    # Physics Model A
    alpha_A, beta_A, gamma_A = reg_A.coef_
    pred_u_A = alpha_A * ocean_u + beta_A * wind_u + gamma_A * iceberg_u
    pred_v_A = alpha_A * ocean_v + beta_A * wind_v + gamma_A * iceberg_v
    y_phys_A = np.column_stack([pred_u_A * delta_t_s, pred_v_A * delta_t_s])
    
    # Physics Model B
    alpha_B, beta_B, gamma_B = reg_B.coef_
    env_factor = 1.0 - siconc
    pred_u_B = env_factor * (alpha_B * ocean_u + beta_B * wind_u) + gamma_B * iceberg_u
    pred_v_B = env_factor * (alpha_B * ocean_v + beta_B * wind_v) + gamma_B * iceberg_v
    y_phys_B = np.column_stack([pred_u_B * delta_t_s, pred_v_B * delta_t_s])
    
    # Vanilla LSTM
    target_scaler = joblib.load('models/preprocessing/target_scaler.pkl')
    checkpoint = torch.load('models/checkpoints/lstm_baseline_best.pt', map_location='cpu')
    model = BaselineLSTM(
        input_size=checkpoint['model_config']['input_size'],
        hidden_size=checkpoint['model_config']['hidden_size'],
        num_layers=checkpoint['model_config']['num_layers'],
        output_size=checkpoint['model_config']['output_size']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    with torch.no_grad():
        lstm_preds_scaled = model(torch.tensor(X_test_scaled.astype(np.float32))).numpy()
    y_lstm = target_scaler.inverse_transform(lstm_preds_scaled)
    
    # Stationary vs Moving threshold
    # Define stationary as iceberg velocity < 0.01 m/s (last obs)
    vel_ms = X_test_phys[:, -1, 2]
    is_stat = vel_ms < 0.01
    
    # Metric computer
    def calc_metrics(y_t, y_p):
        if len(y_t) == 0:
            return {k: np.nan for k in ['MAE_m', 'RMSE_m', 'Mean_EPE_m', 'Median_EPE_m', 'P90_EPE_m', 'P95_EPE_m']}
        epe = euclidean_error(y_t, y_p)
        mae = mean_absolute_error(y_t, y_p)
        rmse = np.sqrt(mean_squared_error(y_t, y_p))
        return {
            'MAE_m': mae,
            'RMSE_m': rmse,
            'Mean_EPE_m': np.mean(epe),
            'Median_EPE_m': np.median(epe),
            'P90_EPE_m': np.percentile(epe, 90),
            'P95_EPE_m': np.percentile(epe, 95)
        }
        
    models_dict = {
        'Persistence': y_pers,
        'Constant Velocity': y_cv,
        'Physics Model A': y_phys_A,
        'Physics Model B': y_phys_B,
        'Vanilla LSTM': y_lstm
    }
    
    results = []
    for m_name, preds in models_dict.items():
        all_m = calc_metrics(y_test_raw, preds)
        stat_m = calc_metrics(y_test_raw[is_stat], preds[is_stat])
        move_m = calc_metrics(y_test_raw[~is_stat], preds[~is_stat])
        
        results.append({
            'Model': m_name,
            'Subset': 'All',
            **all_m
        })
        results.append({
            'Model': m_name,
            'Subset': 'Stationary (<0.01m/s)',
            **stat_m
        })
        results.append({
            'Model': m_name,
            'Subset': 'Moving (>=0.01m/s)',
            **move_m
        })
        
    df_results = pd.DataFrame(results)
    
    docs_dir = Path('docs')
    docs_dir.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(docs_dir / 'physics_baseline_results.csv', index=False)
    
    print("\n--- TEST SET METRICS ---")
    df_all = df_results[df_results['Subset'] == 'All']
    print(df_all.to_markdown(index=False, floatfmt=".2f"))
    
    # Plotting
    figs_dir = Path('docs/figures')
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    for m_name, preds in models_dict.items():
        epe = euclidean_error(y_test_raw, preds)
        sns.kdeplot(epe / 1000, label=m_name, fill=True, alpha=0.2)
        
    plt.xlabel("Endpoint Error (km)")
    plt.ylabel("Density")
    plt.title("Physics Baselines vs LSTM: Endpoint Error Distribution")
    plt.legend()
    plt.xlim(0, 300) # clip for readability
    plt.tight_layout()
    plt.savefig(figs_dir / 'physics_baseline_comparison.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    reg_A, reg_B, unscale_X = fit_physics_models()
    evaluate_on_test(reg_A, reg_B, unscale_X)
