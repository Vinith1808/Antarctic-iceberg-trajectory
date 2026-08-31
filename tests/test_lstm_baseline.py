import pytest
import torch
import numpy as np

from src.modeling.dataset import get_dataloaders, IcebergSequenceDataset
from src.modeling.lstm import BaselineLSTM
from src.modeling.train import count_parameters

def test_model_shapes():
    model = BaselineLSTM(input_size=22, hidden_size=128, num_layers=2, output_size=2)
    x = torch.randn(32, 10, 22)
    out = model(x)
    assert out.shape == (32, 2), f"Expected output shape (32, 2), got {out.shape}"

def test_no_nan_inf_output():
    model = BaselineLSTM()
    x = torch.randn(16, 10, 22)
    out = model(x)
    assert not torch.isnan(out).any(), "Model produced NaN output"
    assert not torch.isinf(out).any(), "Model produced Inf output"

def test_dataloaders():
    train_loader, val_loader, test_loader, target_scaler = get_dataloaders(batch_size=32)
    
    from torch.utils.data import RandomSampler, SequentialSampler
    assert isinstance(train_loader.sampler, RandomSampler), "Train loader must shuffle"
    assert isinstance(val_loader.sampler, SequentialSampler), "Validation loader must not shuffle"
    assert isinstance(test_loader.sampler, SequentialSampler), "Test loader must not shuffle"
    
    # Check one batch
    for X_batch, y_batch in train_loader:
        assert X_batch.shape[1] == 10, "Sequence length must be 10"
        assert X_batch.shape[2] == 22, "Input feature size must be 22"
        assert y_batch.shape[1] == 2, "Target size must be 2"
        assert X_batch.dtype == torch.float32, "Input tensor must be float32"
        assert y_batch.dtype == torch.float32, "Target tensor must be float32"
        break

def test_parameter_count():
    model = BaselineLSTM()
    num_params = count_parameters(model)
    print(f"Total trainable parameters: {num_params}")
    # Basic sanity check: should be > 0 and < 1M for a small baseline
    assert 0 < num_params < 1000000, "Unreasonable parameter count"

def test_test_data_not_in_train():
    # Verify train dataloader pulls exactly from train.npz
    train_ds = IcebergSequenceDataset('data/processed/sequences/train.npz')
    test_ds = IcebergSequenceDataset('data/processed/sequences/test.npz')
    
    assert len(train_ds) == 810, "Expected 810 training samples"
    assert len(test_ds) == 252, "Expected 252 testing samples"

def test_target_scaler_fitted_on_train_only():
    from src.modeling.dataset import IcebergSequenceDataset
    from pathlib import Path
    import joblib
    
    scaler_path = Path('models/preprocessing/target_scaler.pkl')
    assert scaler_path.exists(), "Target scaler not found"
    
    scaler = joblib.load(scaler_path)
    
    # Train dataset with fit_scaler=False should output scaled targets
    train_ds = IcebergSequenceDataset('data/processed/sequences/train.npz', fit_scaler=False)
    
    # Inverse transform should approx equal original targets
    import numpy as np
    y_raw = np.nan_to_num(np.load('data/processed/sequences/train.npz')['y'], nan=0.0).astype(np.float32)
    y_scaled = train_ds.y
    y_reconstructed = scaler.inverse_transform(y_scaled)
    
    np.testing.assert_array_almost_equal(y_raw, y_reconstructed, decimal=1)

