# Phase 8.4.1: PyTorch LSTM Baseline

## 1. Architecture
* **Type:** Vanilla LSTM
* **Layers:** 2
* **Hidden Size:** 128
* **Dropout:** 0.2 (applied between LSTM layers)
* **Final Layer:** A standard fully-connected `Linear` layer mapping the final timestep's hidden state to the 2D prediction target.
* **Parameter Count:** ~210,434 trainable parameters.

## 2. Shapes
* **Input Shape:** `(Batch_Size, 10, 22)`
* **Output Shape:** `(Batch_Size, 2)`

## 3. Features
The ordering strictly matches Phase 8.3:
1. `latitude`
2. `longitude`
3. `velocity_ms`
4. `heading_deg`
5. `distance_m`
6. `uo`
7. `vo`
8. `current_speed_ms`
9. `current_direction_deg`
10. `u10`
11. `v10`
12. `wind_speed_ms`
13. `wind_direction_deg`
14. `siconc`
15. `time_since_previous_observation_hours`
16. `month_sin`
17. `month_cos`
18. `day_of_year_sin`
19. `day_of_year_cos`
20. `current_available`
21. `wind_available`
22. `seaice_available`

## 4. Hyperparameters & Optimization
* **Loss Function:** `MSELoss`
* **Optimizer:** `Adam`
* **Learning Rate:** `1e-3`
* **Batch Size:** `32`
* **Train Shuffle:** `True`
* **Val/Test Shuffle:** `False`

## 5. Training Methodology
* **Early Stopping:** Configured with a patience of 10 epochs.
* **Validation:** Evaluated at the end of every epoch. Only the model state associated with the absolute minimum validation loss is saved.
* **Leakage Prevention:** Test dataset is never accessed during training, tuning, or saving operations.
* **Random Seed:** Set explicitly to `42` across Python, NumPy, and PyTorch (CPU and CUDA) for complete reproducibility.

## 6. Checkpointing
* **Location:** `models/checkpoints/lstm_baseline.pt`
* **Contents:** Contains the model state dict, optimizer state dict, best validation loss, explicit model config dictionary, and random seed value.

## 7. Results (Smoke Test)
* **Epochs run:** 2
* **Train Loss:** (Logged in output)
* **Validation Loss:** (Logged in output)
* **Test results:** All PyTest validations (`tests/test_lstm_baseline.py`) completely passed.

## 8. Hardware
* The pipeline automatically falls back to CPU if CUDA is unavailable, verified on the local host.
