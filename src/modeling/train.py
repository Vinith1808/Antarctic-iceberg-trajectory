import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import random
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

from src.modeling.dataset import get_dataloaders
from src.modeling.lstm import BaselineLSTM

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def calculate_metrics(y_true, y_pred, scaler):
    y_true_unscaled = scaler.inverse_transform(y_true)
    y_pred_unscaled = scaler.inverse_transform(y_pred)
    
    mae = mean_absolute_error(y_true_unscaled, y_pred_unscaled)
    rmse = np.sqrt(mean_squared_error(y_true_unscaled, y_pred_unscaled))
    return mae, rmse

def train_model(smoke_test=False):
    seed = 42
    set_seed(seed)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    train_loader, val_loader, _, target_scaler = get_dataloaders(batch_size=32)
    
    model = BaselineLSTM().to(device)
    print(f"Model parameters: {count_parameters(model)}")
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 2 if smoke_test else 100
    patience = 15
    best_val_loss = float('inf')
    epochs_no_improve = 0
    best_epoch = 0
    
    checkpoints_dir = Path('models/checkpoints')
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoints_dir / 'lstm_baseline_best.pt'
    
    history = []
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        train_preds, train_targets = [], []
        
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * X_batch.size(0)
            
            train_preds.append(outputs.detach().cpu().numpy())
            train_targets.append(y_batch.detach().cpu().numpy())
            
        train_loss /= len(train_loader.dataset)
        train_preds = np.vstack(train_preds)
        train_targets = np.vstack(train_targets)
        train_mae, train_rmse = calculate_metrics(train_targets, train_preds, target_scaler)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_preds, val_targets = [], []
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                val_loss += loss.item() * X_batch.size(0)
                
                val_preds.append(outputs.cpu().numpy())
                val_targets.append(y_batch.cpu().numpy())
                
        val_loss /= len(val_loader.dataset)
        val_preds = np.vstack(val_preds)
        val_targets = np.vstack(val_targets)
        val_mae, val_rmse = calculate_metrics(val_targets, val_preds, target_scaler)
        
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f} | Val MAE: {val_mae:.2f}m")
        
        history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'train_MAE_m': train_mae,
            'val_MAE_m': val_mae,
            'train_RMSE_m': train_rmse,
            'val_RMSE_m': val_rmse
        })
        
        # Early stopping & Checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            best_epoch = epoch + 1
            
            # Save strictly the best model
            torch.save({
                'epoch': best_epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_validation_loss': best_val_loss,
                'model_config': {
                    'input_size': model.input_size,
                    'hidden_size': model.hidden_size,
                    'num_layers': model.num_layers,
                    'output_size': model.output_size
                },
                'random_seed': seed,
                'target_scaler_path': 'models/preprocessing/target_scaler.pkl'
            }, checkpoint_path)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience and not smoke_test:
                print(f"Early stopping triggered after {epoch+1} epochs.")
                break
                
    print(f"Training completed. Best Val Loss: {best_val_loss:.4f} at epoch {best_epoch}")
    
    # Save history
    docs_dir = Path('docs')
    docs_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(docs_dir / 'lstm_training_history.csv', index=False)
    
    return model, train_loss, best_val_loss, best_epoch, history

if __name__ == '__main__':
    train_model(smoke_test=False)
