import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib

class IcebergSequenceDataset(Dataset):
    def __init__(self, npz_path, fit_scaler=False):
        data = np.load(npz_path)
        self.X = np.nan_to_num(data['X'], nan=0.0).astype(np.float32)
        y_raw = np.nan_to_num(data['y'], nan=0.0).astype(np.float32)
        
        # Target scaling
        scaler_path = Path('models/preprocessing/target_scaler.pkl')
        if fit_scaler:
            self.target_scaler = StandardScaler()
            self.target_scaler.fit(y_raw)
            scaler_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.target_scaler, scaler_path)
        else:
            self.target_scaler = joblib.load(scaler_path)
            
        self.y = self.target_scaler.transform(y_raw).astype(np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])

def get_dataloaders(data_dir='data/processed/sequences', batch_size=32):
    data_dir = Path(data_dir)
    
    # Fit the scaler ONLY on the train dataset
    train_dataset = IcebergSequenceDataset(data_dir / 'train.npz', fit_scaler=True)
    val_dataset = IcebergSequenceDataset(data_dir / 'validation.npz', fit_scaler=False)
    test_dataset = IcebergSequenceDataset(data_dir / 'test.npz', fit_scaler=False)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader, train_dataset.target_scaler
