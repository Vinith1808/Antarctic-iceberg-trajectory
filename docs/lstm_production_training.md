# Phase 8.4.2: Leakage-Safe Production Training of Baseline LSTM

## 1. Target Normalization Methodology
* **Implementation:** A `StandardScaler` was fit strictly on the raw physical target displacements (`target_dx_m`, `target_dy_m`) derived uniquely from the `train.npz` tensors.
* **Leakage-Safe Validation:** A pytest assertion validates that validation and test dataset sequences load cleanly, whilst ensuring their target labels are only transformed using the scale generated from training constraints.
* **Scaler Parameters:**
  * Mean `[dx, dy]`: `[-8288.10, 4134.76]`
  * Scale `[dx, dy]`: `[42530.10, 34498.35]`

## 2. Architecture & Hyperparameters
* **Model:** Vanilla LSTM
* **Number of Layers:** 2
* **Hidden Size:** 128
* **Input Size:** 22
* **Output Size:** 2
* **Dropout:** 0.2
* **Optimizer:** Adam
* **Learning Rate:** 1e-3
* **Loss Function:** MSELoss
* **Batch Size:** 32
* **Random Seed:** 42

## 3. Training Execution & Metrics
* **Hardware:** CPU
* **Max Epochs Limit:** 100
* **Early Stopping Configuration:** Patience of 15 epochs without validation loss improvement.
* **Total Epochs Completed:** 29 (Early stopping triggered)
* **Best Model Checkpoint:** Epoch 14
* **Best Validation Loss (Scaled MSE):** 0.3598
* **Best Validation MAE (Physical Meters):** 11,293.48 m (~11.3 km)
* **Best Validation RMSE (Physical Meters):** 22,749.73 m (~22.7 km)
* **Corresponding Train MAE (Physical Meters):** 11,379.03 m
* **Corresponding Train RMSE (Physical Meters):** 25,309.95 m

## 4. Output Artifacts
* **Checkpoint saved:** `models/checkpoints/lstm_baseline_best.pt`
  * Contents: Model weights, optimizer config, configuration dictionaries, and best metrics.
* **History Log:** `docs/lstm_training_history.csv`
* **Target Scaler Checkpoint:** `models/preprocessing/target_scaler.pkl`
