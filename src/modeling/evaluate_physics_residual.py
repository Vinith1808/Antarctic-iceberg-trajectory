import numpy as np
import pandas as pd
import joblib
import torch
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.modeling.physics_residual_lstm import PhysicsResidualLSTM
from src.modeling.lstm import BaselineLSTM
from src.modeling.physics_baseline import fit_physics_models, get_physics_features
from src.modeling.evaluate_baselines import euclidean_error
from src.modeling.train_physics_residual import get_physics_predictions

def main():
    # 1. Load data
    test_data = np.load('data/processed/sequences/test.npz')
    X_test_scaled = np.nan_to_num(test_data['X'], nan=0.0)
    y_test_raw = np.nan_to_num(test_data['y'], nan=0.0)
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    # 2. Get Physics Baselines (A and B)
    reg_A, reg_B, unscale_X = fit_physics_models()
    p_test_A, _ = get_physics_predictions(X_test_scaled, y_test_raw, test_meta, reg_A, unscale_X, is_model_B=False)
    p_test_B, _ = get_physics_predictions(X_test_scaled, y_test_raw, test_meta, reg_B, unscale_X, is_model_B=True)
    
    # 3. Get Persistence & Constant Velocity
    N = len(y_test_raw)
    y_pers = np.zeros((N, 2))
    
    X_test_phys = unscale_X(X_test_scaled)
    iceberg_u, iceberg_v, _, _, _, _, _, delta_t_s = get_physics_features(X_test_phys, test_meta)
    y_cv = np.column_stack([iceberg_u * delta_t_s, iceberg_v * delta_t_s])
    
    # 4. Get Vanilla LSTM
    target_scaler = joblib.load('models/preprocessing/target_scaler.pkl')
    vanilla_ckpt = torch.load('models/checkpoints/lstm_baseline_best.pt', map_location='cpu')
    vanilla_model = BaselineLSTM(
        input_size=vanilla_ckpt['model_config']['input_size'],
        hidden_size=vanilla_ckpt['model_config']['hidden_size'],
        num_layers=vanilla_ckpt['model_config']['num_layers'],
        output_size=vanilla_ckpt['model_config']['output_size']
    )
    vanilla_model.load_state_dict(vanilla_ckpt['model_state_dict'])
    vanilla_model.eval()
    
    with torch.no_grad():
        lstm_preds_scaled = vanilla_model(torch.tensor(X_test_scaled.astype(np.float32))).numpy()
    y_vanilla_lstm = target_scaler.inverse_transform(lstm_preds_scaled)
    
    # 5. Get Physics + Residual LSTM
    resid_ckpt = torch.load('models/checkpoints/physics_residual_lstm_best.pt', map_location='cpu')
    resid_scaler_r = joblib.load('models/preprocessing/residual_target_scaler.pkl')
    resid_scaler_p = joblib.load('models/preprocessing/physics_pred_scaler.pkl')
    
    resid_model = PhysicsResidualLSTM(
        input_size=resid_ckpt['model_config']['input_size'],
        hidden_size=resid_ckpt['model_config']['hidden_size'],
        num_layers=resid_ckpt['model_config']['num_layers'],
        dropout=resid_ckpt['model_config']['dropout']
    )
    resid_model.load_state_dict(resid_ckpt['model_state_dict'])
    resid_model.eval()
    
    is_model_B = resid_ckpt['model_config']['is_model_B']
    base_physics_preds = p_test_B if is_model_B else p_test_A
    
    base_physics_preds_scaled = resid_scaler_p.transform(base_physics_preds)
    
    with torch.no_grad():
        resid_preds_scaled = resid_model(
            torch.tensor(X_test_scaled.astype(np.float32)), 
            torch.tensor(base_physics_preds_scaled.astype(np.float32))
        ).numpy()
        
    resid_preds_raw = resid_scaler_r.inverse_transform(resid_preds_scaled)
    y_residual_lstm = base_physics_preds + resid_preds_raw
    
    # 6. Evaluation metrics computation
    vel_ms = X_test_phys[:, -1, 2]
    is_stat = vel_ms < 0.01
    
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
        'Physics Model A': p_test_A,
        'Physics Model B': p_test_B,
        'Vanilla LSTM': y_vanilla_lstm,
        'Physics + Residual LSTM': y_residual_lstm
    }
    
    results = []
    for m_name, preds in models_dict.items():
        all_m = calc_metrics(y_test_raw, preds)
        stat_m = calc_metrics(y_test_raw[is_stat], preds[is_stat])
        move_m = calc_metrics(y_test_raw[~is_stat], preds[~is_stat])
        
        results.append({'Model': m_name, 'Subset': 'All', **all_m})
        results.append({'Model': m_name, 'Subset': 'Stationary (<0.01m/s)', **stat_m})
        results.append({'Model': m_name, 'Subset': 'Moving (>=0.01m/s)', **move_m})
        
    df_results = pd.DataFrame(results)
    
    docs_dir = Path('docs')
    docs_dir.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(docs_dir / 'physics_residual_results.csv', index=False)
    
    print("\n--- TEST SET METRICS ---")
    df_all = df_results[df_results['Subset'] == 'All']
    print(df_all.to_markdown(index=False, floatfmt=".2f"))
    
    # 7. Calculate Percentage Improvements over baselines
    resid_epe = float(df_all[df_all['Model'] == 'Physics + Residual LSTM']['Mean_EPE_m'].iloc[0])
    print("\n--- PERCENTAGE IMPROVEMENT ---")
    for m_name in ['Persistence', 'Constant Velocity', 'Physics Model A', 'Physics Model B', 'Vanilla LSTM']:
        base_epe = float(df_all[df_all['Model'] == m_name]['Mean_EPE_m'].iloc[0])
        imp = (base_epe - resid_epe) / base_epe * 100
        print(f"vs {m_name}: {imp:.2f}%")
        
    # 8. Stationary Iceberg Check
    # Calculate magnitude of predicted displacement for stationary cases
    y_res_stat = y_residual_lstm[is_stat]
    disp_mag = np.sqrt(y_res_stat[:,0]**2 + y_res_stat[:,1]**2)
    
    mean_disp = np.mean(disp_mag)
    med_disp = np.median(disp_mag)
    pct_1km = np.mean(disp_mag > 1000) * 100
    pct_5km = np.mean(disp_mag > 5000) * 100
    
    print("\n--- STATIONARY CHECK (Physics + Residual LSTM) ---")
    print(f"Mean predicted displacement: {mean_disp:.2f} m")
    print(f"Median predicted displacement: {med_disp:.2f} m")
    print(f"% exceeding 1 km: {pct_1km:.2f}%")
    print(f"% exceeding 5 km: {pct_5km:.2f}%")
    
    # Compare with Persistence (exactly 0) and Physics B
    y_physB_stat = p_test_B[is_stat]
    physB_mag = np.sqrt(y_physB_stat[:,0]**2 + y_physB_stat[:,1]**2)
    print(f"Physics B Mean displacement: {np.mean(physB_mag):.2f} m")
    
    # 9. Plotting
    figs_dir = Path('docs/figures')
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    for m_name, preds in models_dict.items():
        epe = euclidean_error(y_test_raw, preds)
        sns.kdeplot(epe / 1000, label=m_name, fill=True, alpha=0.2)
        
    plt.xlabel("Endpoint Error (km)")
    plt.ylabel("Density")
    plt.title("Physics Residual LSTM vs Baselines: Endpoint Error Distribution")
    plt.legend()
    plt.xlim(0, 300) # clip for readability
    plt.tight_layout()
    plt.savefig(figs_dir / 'physics_residual_comparison.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    main()
