import torch
import torch.nn as nn

class BaselineLSTM(nn.Module):
    def __init__(self, input_size=22, hidden_size=128, num_layers=2, dropout=0.2, output_size=2):
        super(BaselineLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        # Batch first means input is (batch_size, seq_len, features)
        self.lstm = nn.LSTM(
            input_size=input_size, 
            hidden_size=hidden_size, 
            num_layers=num_layers, 
            batch_first=True, 
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # We want the output from the last timestep
        # lstm_out shape: (batch_size, seq_len, hidden_size)
        last_timestep_out = lstm_out[:, -1, :]
        
        # Pass through fully connected layer
        # out shape: (batch_size, output_size)
        out = self.fc(last_timestep_out)
        return out
