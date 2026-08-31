# Phase 8.5: Baseline Comparison & Test Evaluation

## 1. Objective
To evaluate whether the trained LSTM baseline model meaningfully outperforms simple physics and naïve baselines on the strictly held-out test dataset, avoiding any information leakage.

## 2. Test Dataset
* **Data Source:** `data/processed/sequences/test.npz`
* **Sequence Count:** 252 observations
* **Leakage Constraints:** Test sequences were absolutely isolated from scaler fitting and model training.

## 3. Baselines
* **Persistence Baseline:** Predicts future spatial displacement as precisely 0 meters (assuming the iceberg stays exactly where it was at the end of the sequence).
* **Constant Velocity Baseline:** Uses the last recorded physical velocity (`velocity_ms`) and heading (`heading_deg`), projecting displacement over the `target_time_delta_hours`.
  * Math: `dx = v * dt * sin(heading)`, `dy = v * dt * cos(heading)`

## 4. LSTM Baseline
* PyTorch architecture initialized from `models/checkpoints/lstm_baseline_best.pt`.
* Unscaled test data features injected; output reversed via `models/preprocessing/target_scaler.pkl` to compute exact meter discrepancy.

## 5. Results Table

| Model             |   MAE_dx_m |   MAE_dy_m |   RMSE_dx_m |   RMSE_dy_m |   Mean_EPE_m |   Median_EPE_m |   P95_EPE_m |
|:------------------|-----------:|-----------:|------------:|------------:|-------------:|---------------:|------------:|
| Persistence       |    9601.53 |   12172.69 |    28510.45 |    33373.00 |     17089.97 |           0.00 |   119429.91 |
| Constant Velocity |   13101.26 |  297099.31 |    35063.87 |   695880.35 |    298199.31 |        1985.75 |  1452809.88 |
| LSTM              |   12359.14 |   11667.29 |    27268.48 |    29589.72 |     19234.16 |        3941.58 |   104521.70 |

## 6. Improvements
* **LSTM Mean Improvement over Persistence:** -12.55%
* **LSTM Mean Improvement over Const. Velocity:** 93.55%

## 7. Per-Iceberg Generalization

| iceberg_id   |   number_of_test_sequences |   persistence_mean_error |   constant_velocity_mean_error |   lstm_mean_error |
|:-------------|---------------------------:|-------------------------:|-------------------------------:|------------------:|
| a23a         |                         19 |                  6831.82 |                      235850.90 |          11914.76 |
| a81          |                         16 |                 53304.37 |                      823479.02 |          39425.58 |
| b09b         |                         33 |                   347.27 |                       69296.98 |           2563.10 |
| b28          |                         18 |                     0.00 |                           0.00 |           2970.10 |
| b46          |                         18 |                 49399.73 |                      766882.17 |          45116.54 |
| c15          |                         34 |                   547.80 |                      101889.55 |           3017.69 |
| c18c         |                         15 |                  2525.56 |                      148282.65 |          47362.44 |
| c24          |                         36 |                     0.00 |                           0.00 |           3048.94 |
| c35          |                         32 |                  3255.23 |                      231538.63 |           4279.20 |
| d27          |                         18 |                116596.85 |                     1548190.11 |         101408.78 |
| d30b         |                         13 |                 12609.50 |                       33351.83 |          11891.01 |

## 8. Conclusions
*(See table above for results)*. If the LSTM failed to beat the constant velocity baseline (or even persistence), it indicates that learning simple sequential correlations directly via MSE loss is insufficient for iceberg drift, likely due to high autocorrelation and chaotic physical drivers overriding simple sequential dependencies. We must evaluate whether complex physics integration is necessary.
