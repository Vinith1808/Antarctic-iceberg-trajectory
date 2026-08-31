import pytest
import torch
import numpy as np
import pandas as pd
from src.modeling.physics_residual_lstm import PhysicsResidualLSTM
from src.modeling.train_physics_residual import get_physics_predictions, ResidualDataset
from src.modeling.physics_baseline import fit_physics_models
from torch.utils.data import DataLoader

def test_residual_lstm_shapes():
    batch = 32
    seq = 10
    feat = 22
    
    model = PhysicsResidualLSTM(feat, 128, 2, dropout=0.2)
    
    x = torch.randn(batch, seq, feat)
    p = torch.randn(batch, 2)
    
    out = model(x, p)
    
    assert out.shape == (batch, 2)
    assert not torch.isnan(out).any()

def test_residual_target_equation():
    y_raw = np.array([[1000.0, 500.0]])
    physics_preds = np.array([[800.0, 600.0]])
    
    residuals = y_raw - physics_preds
    
    assert residuals[0, 0] == 200.0
    assert residuals[0, 1] == -100.0
    
    # Final prediction equation
    predicted_residual = np.array([[150.0, -80.0]])
    final_pred = physics_preds + predicted_residual
    
    assert final_pred[0, 0] == 950.0
    assert final_pred[0, 1] == 520.0

def test_physics_residual_dataloader():
    X = np.random.randn(10, 10, 22)
    p = np.random.randn(10, 2)
    r = np.random.randn(10, 2)
    
    dataset = ResidualDataset(X, p, r)
    loader = DataLoader(dataset, batch_size=2)
    
    for X_b, p_b, r_b in loader:
        assert X_b.shape == (2, 10, 22)
        assert p_b.shape == (2, 2)
        assert r_b.shape == (2, 2)
        break
