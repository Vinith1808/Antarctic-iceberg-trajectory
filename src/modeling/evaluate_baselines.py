import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error

from src.modeling.lstm import BaselineLSTM

def euclidean_error(y_true, y_pred):
    return np.sqrt(np.sum((y_true - y_pred)**2, axis=1))

def evaluate_models():
    # Load Test Data
    test_data = np.load('data/processed/sequences/test.npz')
    X_test = test_data['X'] # Shape: (N, 10, 22)
    y_test = test_data['y'] # Shape: (N, 2), raw meters
    
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    
    N = len(X_test)
    print(f"Evaluated sequences: {N}")
    
    # Target Data
    true_dx = y_test[:, 0]
    true_dy = y_test[:, 1]
    
    # --------------------------------------------------
    # 1. Persistence Baseline
    # --------------------------------------------------
    pers_dx = np.zeros(N)
    pers_dy = np.zeros(N)
    y_pers = np.column_stack([pers_dx, pers_dy])
    
    # --------------------------------------------------
    # 2. Constant Velocity Baseline
    # --------------------------------------------------
    # Index 2: velocity_ms, Index 3: heading_deg
    velocity_ms = X_test[:, -1, 2]
    heading_deg = X_test[:, -1, 3]
    time_delta_s = test_meta['target_time_delta_hours'].values * 3600.0
    
    # Heading convention: 0=North (dy), 90=East (dx)
    # dx = v * dt * sin(heading), dy = v * dt * cos(heading)
    cv_dx = velocity_ms * time_delta_s * np.sin(np.radians(heading_deg))
    cv_dy = velocity_ms * time_delta_s * np.cos(np.radians(heading_deg))
    
    # If heading is NaN (e.g. zero movement previously), displacement is zero.
    cv_dx = np.nan_to_num(cv_dx, nan=0.0)
    cv_dy = np.nan_to_num(cv_dy, nan=0.0)
    
    y_cv = np.column_stack([cv_dx, cv_dy])
    
    # --------------------------------------------------
    # 3. LSTM Baseline
    # --------------------------------------------------
    # Load Scaler
    target_scaler = joblib.load('models/preprocessing/target_scaler.pkl')
    
    # Load Model
    checkpoint = torch.load('models/checkpoints/lstm_baseline_best.pt', map_location='cpu')
    model = BaselineLSTM(
        input_size=checkpoint['model_config']['input_size'],
        hidden_size=checkpoint['model_config']['hidden_size'],
        num_layers=checkpoint['model_config']['num_layers'],
        output_size=checkpoint['model_config']['output_size']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Since test contains NaNs initially (before Dataset __init__), we nan_to_num
    X_test_clean = np.nan_to_num(X_test, nan=0.0).astype(np.float32)
    with torch.no_grad():
        lstm_preds_scaled = model(torch.tensor(X_test_clean)).numpy()
        
    y_lstm = target_scaler.inverse_transform(lstm_preds_scaled)
    
    # --------------------------------------------------
    # Metric Calculation Function
    # --------------------------------------------------
    def get_metrics(y_true, y_pred):
        mae_dx = mean_absolute_error(y_true[:,0], y_pred[:,0])
        mae_dy = mean_absolute_error(y_true[:,1], y_pred[:,1])
        rmse_dx = np.sqrt(mean_squared_error(y_true[:,0], y_pred[:,0]))
        rmse_dy = np.sqrt(mean_squared_error(y_true[:,1], y_pred[:,1]))
        
        epe = euclidean_error(y_true, y_pred)
        mean_epe = np.mean(epe)
        median_epe = np.median(epe)
        p95_epe = np.percentile(epe, 95)
        
        return {
            'MAE_dx_m': mae_dx,
            'MAE_dy_m': mae_dy,
            'RMSE_dx_m': rmse_dx,
            'RMSE_dy_m': rmse_dy,
            'Mean_EPE_m': mean_epe,
            'Median_EPE_m': median_epe,
            'P95_EPE_m': p95_epe
        }
    
    pers_metrics = get_metrics(y_test, y_pers)
    cv_metrics = get_metrics(y_test, y_cv)
    lstm_metrics = get_metrics(y_test, y_lstm)
    
    df_metrics = pd.DataFrame([
        {'Model': 'Persistence', **pers_metrics},
        {'Model': 'Constant Velocity', **cv_metrics},
        {'Model': 'LSTM', **lstm_metrics}
    ])
    
    print("\n--- RESULTS TABLE ---")
    print(df_metrics.to_markdown(index=False, floatfmt=".2f"))
    
    # Calculate improvements
    imp_mean_pers = (pers_metrics['Mean_EPE_m'] - lstm_metrics['Mean_EPE_m']) / pers_metrics['Mean_EPE_m'] * 100
    imp_mean_cv = (cv_metrics['Mean_EPE_m'] - lstm_metrics['Mean_EPE_m']) / cv_metrics['Mean_EPE_m'] * 100
    
    print(f"\nLSTM Mean Improvement over Persistence: {imp_mean_pers:.2f}%")
    print(f"LSTM Mean Improvement over Const. Vel: {imp_mean_cv:.2f}%")
    
    # --------------------------------------------------
    # Per-Iceberg Analysis
    # --------------------------------------------------
    epe_pers = euclidean_error(y_test, y_pers)
    epe_cv = euclidean_error(y_test, y_cv)
    epe_lstm = euclidean_error(y_test, y_lstm)
    
    df_iceberg = pd.DataFrame({
        'iceberg_id': test_meta['iceberg_id'],
        'EPE_pers': epe_pers,
        'EPE_cv': epe_cv,
        'EPE_lstm': epe_lstm
    })
    
    iceberg_summary = df_iceberg.groupby('iceberg_id').agg(
        number_of_test_sequences=('EPE_pers', 'count'),
        persistence_mean_error=('EPE_pers', 'mean'),
        constant_velocity_mean_error=('EPE_cv', 'mean'),
        lstm_mean_error=('EPE_lstm', 'mean')
    ).reset_index()
    
    print("\n--- PER-ICEBERG SUMMARY ---")
    print(iceberg_summary.to_markdown(index=False, floatfmt=".2f"))
    
    # --------------------------------------------------
    # Visualizations
    # --------------------------------------------------
    figs_dir = Path('docs/figures')
    figs_dir.mkdir(parents=True, exist_ok=True)
    
    # Endpoint Error Distribution
    plt.figure(figsize=(10, 6))
    sns.kdeplot(epe_pers / 1000, label='Persistence', fill=True, alpha=0.3)
    sns.kdeplot(epe_cv / 1000, label='Constant Velocity', fill=True, alpha=0.3)
    sns.kdeplot(epe_lstm / 1000, label='LSTM Baseline', fill=True, alpha=0.3)
    plt.xlabel("Endpoint Error (km)")
    plt.ylabel("Density")
    plt.title("Test Set Endpoint Error Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figs_dir / 'test_endpoint_error_comparison.png', dpi=300)
    plt.close()
    
    # Trajectory plots
    # We will plot the actual vs predicted displacements relative to origin (0,0)
    # Pick 5 diverse sequences
    np.random.seed(42)
    indices = np.random.choice(N, min(5, N), replace=False)
    
    for i, idx in enumerate(indices):
        plt.figure(figsize=(6, 6))
        
        plt.plot(0, 0, 'ko', markersize=8, label='Sequence End (Origin)')
        
        # True Target
        plt.plot(y_test[idx, 0] / 1000, y_test[idx, 1] / 1000, 'g*', markersize=12, label='Actual Target')
        plt.plot([0, y_test[idx, 0] / 1000], [0, y_test[idx, 1] / 1000], 'g--', alpha=0.5)
        
        # Pers Target
        plt.plot(y_pers[idx, 0] / 1000, y_pers[idx, 1] / 1000, 'rs', markersize=8, label='Persistence')
        
        # CV Target
        plt.plot(y_cv[idx, 0] / 1000, y_cv[idx, 1] / 1000, 'b^', markersize=8, label='Const. Velocity')
        plt.plot([0, y_cv[idx, 0] / 1000], [0, y_cv[idx, 1] / 1000], 'b--', alpha=0.5)
        
        # LSTM Target
        plt.plot(y_lstm[idx, 0] / 1000, y_lstm[idx, 1] / 1000, 'mo', markersize=8, label='LSTM')
        plt.plot([0, y_lstm[idx, 0] / 1000], [0, y_lstm[idx, 1] / 1000], 'm--', alpha=0.5)
        
        plt.xlabel('Displacement East (km)')
        plt.ylabel('Displacement North (km)')
        plt.title(f"Trajectory Prediction - Sequence {idx} (Iceberg {test_meta.iloc[idx]['iceberg_id']})")
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(figs_dir / f'trajectory_prediction_example_{i+1}.png', dpi=300)
        plt.close()
        
    # Write Documentation
    md = f"""# Phase 8.5: Baseline Comparison & Test Evaluation

## 1. Objective
To evaluate whether the trained LSTM baseline model meaningfully outperforms simple physics and naïve baselines on the strictly held-out test dataset, avoiding any information leakage.

## 2. Test Dataset
* **Data Source:** `data/processed/sequences/test.npz`
* **Sequence Count:** {N} observations
* **Leakage Constraints:** Test sequences were absolutely isolated from scaler fitting and model training.

## 3. Baselines
* **Persistence Baseline:** Predicts future spatial displacement as precisely 0 meters (assuming the iceberg stays exactly where it was at the end of the sequence).
* **Constant Velocity Baseline:** Uses the last recorded physical velocity (`velocity_ms`) and heading (`heading_deg`), projecting displacement over the `target_time_delta_hours`.
  * Math: `dx = v * dt * sin(heading)`, `dy = v * dt * cos(heading)`

## 4. LSTM Baseline
* PyTorch architecture initialized from `models/checkpoints/lstm_baseline_best.pt`.
* Unscaled test data features injected; output reversed via `models/preprocessing/target_scaler.pkl` to compute exact meter discrepancy.

## 5. Results Table

{df_metrics.to_markdown(index=False, floatfmt=".2f")}

## 6. Improvements
* **LSTM Mean Improvement over Persistence:** {imp_mean_pers:.2f}%
* **LSTM Mean Improvement over Const. Velocity:** {imp_mean_cv:.2f}%

## 7. Per-Iceberg Generalization

{iceberg_summary.to_markdown(index=False, floatfmt=".2f")}

## 8. Conclusions
*(See table above for results)*. If the LSTM failed to beat the constant velocity baseline (or even persistence), it indicates that learning simple sequential correlations directly via MSE loss is insufficient for iceberg drift, likely due to high autocorrelation and chaotic physical drivers overriding simple sequential dependencies. We must evaluate whether complex physics integration is necessary.
"""
    with open('docs/baseline_comparison.md', 'w') as f:
        f.write(md)
        
if __name__ == '__main__':
    evaluate_models()
