import torch
import torch.nn as nn

class PhysicsResidualLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout=0.2):
        """
        Physics-informed Residual LSTM architecture.
        Takes the standard input sequence and an explicit physics-based prediction.
        Predicts the *residual* error of the physics model.
        """
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # We concatenate the LSTM hidden output (size: hidden_size) 
        # with the 2D physics prediction (size: 2) -> total size: hidden_size + 2
        self.fc = nn.Linear(hidden_size + 2, 2)
        
    def forward(self, x, physics_pred):
        """
        x: [batch, seq_len, input_size] - Standard normalized sequence features
        physics_pred: [batch, 2] - Normalized physics-based predictions
        Returns: [batch, 2] - Predicted residual
        """
        out, _ = self.lstm(x)
        last_hidden = out[:, -1, :] # [batch, hidden_size]
        
        combined = torch.cat([last_hidden, physics_pred], dim=1)
        residual = self.fc(combined)
        
        return residual
