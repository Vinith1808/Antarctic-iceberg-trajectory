import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from src.modeling.physics_residual_lstm import PhysicsResidualLSTM
from src.modeling.physics_baseline import fit_physics_models, get_physics_features

class ResidualDataset(Dataset):
    def __init__(self, X, physics_preds, residuals):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.physics_preds = torch.tensor(physics_preds, dtype=torch.float32)
        self.residuals = torch.tensor(residuals, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.physics_preds[idx], self.residuals[idx]

def get_physics_predictions(X_scaled, y_raw, meta, reg, unscale_X, is_model_B=True):
    # Unscale X to physical units
    X_phys = unscale_X(X_scaled)
    
    iceberg_u, iceberg_v, ocean_u, ocean_v, wind_u, wind_v, siconc, delta_t_s = get_physics_features(X_phys, meta)
    
    alpha, beta, gamma = reg.coef_
    if is_model_B:
        env_factor = 1.0 - siconc
        pred_u = env_factor * (alpha * ocean_u + beta * wind_u) + gamma * iceberg_u
        pred_v = env_factor * (alpha * ocean_v + beta * wind_v) + gamma * iceberg_v
    else:
        pred_u = alpha * ocean_u + beta * wind_u + gamma * iceberg_u
        pred_v = alpha * ocean_v + beta * wind_v + gamma * iceberg_v
        
    physics_dx = pred_u * delta_t_s
    physics_dy = pred_v * delta_t_s
    physics_preds = np.column_stack([physics_dx, physics_dy])
    
    # Calculate residuals
    residuals = y_raw - physics_preds
    
    return physics_preds, residuals

def train_model(train_loader, val_loader, input_size, hidden_size, num_layers, dropout, lr, patience, epochs):
    model = PhysicsResidualLSTM(input_size, hidden_size, num_layers, dropout)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    best_val_loss = float('inf')
    best_state = None
    epochs_no_improve = 0
    best_epoch = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for X_batch, p_batch, r_batch in train_loader:
            optimizer.zero_grad()
            preds = model(X_batch, p_batch)
            loss = criterion(preds, r_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * X_batch.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, p_batch, r_batch in val_loader:
                preds = model(X_batch, p_batch)
                loss = criterion(preds, r_batch)
                val_loss += loss.item() * X_batch.size(0)
        val_loss /= len(val_loader.dataset)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = model.state_dict().copy()
            epochs_no_improve = 0
            best_epoch = epoch
        else:
            epochs_no_improve += 1
            
        if epochs_no_improve >= patience:
            break
            
    return best_state, best_val_loss, best_epoch

def main():
    torch.manual_seed(42)
    np.random.seed(42)
    
    # 1. Load Data
    train_data = np.load('data/processed/sequences/train.npz')
    val_data = np.load('data/processed/sequences/validation.npz')
    
    X_train_raw = np.nan_to_num(train_data['X'], nan=0.0)
    y_train_raw = np.nan_to_num(train_data['y'], nan=0.0)
    train_meta = pd.read_parquet('data/processed/sequences/train_meta.parquet')
    
    X_val_raw = np.nan_to_num(val_data['X'], nan=0.0)
    y_val_raw = np.nan_to_num(val_data['y'], nan=0.0)
    val_meta = pd.read_parquet('data/processed/sequences/validation_meta.parquet')
    
    # 2. Get Physics Models
    reg_A, reg_B, unscale_X = fit_physics_models()
    
    # --- Variant B: Without Sea-Ice (Physics A) ---
    p_train_A, r_train_A = get_physics_predictions(X_train_raw, y_train_raw, train_meta, reg_A, unscale_X, is_model_B=False)
    p_val_A, r_val_A = get_physics_predictions(X_val_raw, y_val_raw, val_meta, reg_A, unscale_X, is_model_B=False)
    
    from sklearn.preprocessing import StandardScaler
    scaler_r_A = StandardScaler().fit(r_train_A)
    scaler_p_A = StandardScaler().fit(p_train_A)
    
    train_loader_A = DataLoader(ResidualDataset(X_train_raw, scaler_p_A.transform(p_train_A), scaler_r_A.transform(r_train_A)), batch_size=32, shuffle=True)
    val_loader_A = DataLoader(ResidualDataset(X_val_raw, scaler_p_A.transform(p_val_A), scaler_r_A.transform(r_val_A)), batch_size=32, shuffle=False)
    
    print("Training Variant B (Physics A, No Sea-Ice)...")
    state_A, loss_A, epoch_A = train_model(train_loader_A, val_loader_A, 22, 128, 2, 0.2, 1e-3, 15, 100)
    
    # --- Variant C: With Sea-Ice (Physics B) ---
    p_train_B, r_train_B = get_physics_predictions(X_train_raw, y_train_raw, train_meta, reg_B, unscale_X, is_model_B=True)
    p_val_B, r_val_B = get_physics_predictions(X_val_raw, y_val_raw, val_meta, reg_B, unscale_X, is_model_B=True)
    
    scaler_r_B = StandardScaler().fit(r_train_B)
    scaler_p_B = StandardScaler().fit(p_train_B)
    
    train_loader_B = DataLoader(ResidualDataset(X_train_raw, scaler_p_B.transform(p_train_B), scaler_r_B.transform(r_train_B)), batch_size=32, shuffle=True)
    val_loader_B = DataLoader(ResidualDataset(X_val_raw, scaler_p_B.transform(p_val_B), scaler_r_B.transform(r_val_B)), batch_size=32, shuffle=False)
    
    print("Training Variant C (Physics B, With Sea-Ice)...")
    state_B, loss_B, epoch_B = train_model(train_loader_B, val_loader_B, 22, 128, 2, 0.2, 1e-3, 15, 100)
    
    print("\n--- ABLATION RESULTS (Validation Set) ---")
    print(f"Vanilla LSTM (Epoch 14): MSE ~0.3598 (from Phase 8.4)")
    print(f"Variant B (Physics A) Best Val Loss: {loss_A:.4f} at epoch {epoch_A}")
    print(f"Variant C (Physics B) Best Val Loss: {loss_B:.4f} at epoch {epoch_B}")
    
    # Note: We can't directly compare MSE of residuals to MSE of targets, 
    # since they are scaled differently! 
    # But we can compare Variant B and Variant C since they are similar in scale.
    # To be absolutely sure, let's inverse transform and calculate real RMSE.
    
    # Helper for real validation error
    def eval_real(state, loader, scaler_r, scaler_p, p_val, y_val_raw):
        model = PhysicsResidualLSTM(22, 128, 2, 0.2)
        model.load_state_dict(state)
        model.eval()
        
        all_preds = []
        with torch.no_grad():
            for X_batch, p_batch, _ in loader:
                preds_scaled = model(X_batch, p_batch).numpy()
                all_preds.append(preds_scaled)
        
        preds_scaled = np.vstack(all_preds)
        preds_residual = scaler_r.inverse_transform(preds_scaled)
        
        final_preds = p_val + preds_residual
        mae = np.mean(np.abs(y_val_raw - final_preds))
        return mae
    
    mae_A = eval_real(state_A, val_loader_A, scaler_r_A, scaler_p_A, p_val_A, y_val_raw)
    mae_B = eval_real(state_B, val_loader_B, scaler_r_B, scaler_p_B, p_val_B, y_val_raw)
    print(f"Variant B Real MAE: {mae_A:.2f} m")
    print(f"Variant C Real MAE: {mae_B:.2f} m")
    
    # Select best
    if mae_B <= mae_A:
        print("Selecting Variant C (Physics B) as the final model.")
        final_state = state_B
        final_scaler_r = scaler_r_B
        final_scaler_p = scaler_p_B
        final_epoch = epoch_B
        is_model_B = True
    else:
        print("Selecting Variant B (Physics A) as the final model.")
        final_state = state_A
        final_scaler_r = scaler_r_A
        final_scaler_p = scaler_p_A
        final_epoch = epoch_A
        is_model_B = False
        
    # Save the artifacts
    checkpoint = {
        'model_state_dict': final_state,
        'model_config': {
            'input_size': 22,
            'hidden_size': 128,
            'num_layers': 2,
            'dropout': 0.2,
            'is_model_B': is_model_B
        },
        'best_epoch': final_epoch
    }
    torch.save(checkpoint, 'models/checkpoints/physics_residual_lstm_best.pt')
    
    joblib.dump(final_scaler_r, 'models/preprocessing/residual_target_scaler.pkl')
    joblib.dump(final_scaler_p, 'models/preprocessing/physics_pred_scaler.pkl')
    
    print("\nSaved models/checkpoints/physics_residual_lstm_best.pt")
    print("Saved models/preprocessing/residual_target_scaler.pkl")
    print("Saved models/preprocessing/physics_pred_scaler.pkl")

if __name__ == '__main__':
    main()
