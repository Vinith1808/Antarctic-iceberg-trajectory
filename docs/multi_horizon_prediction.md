# Phase 9: Multi-Horizon Prediction Evaluation

## 1. Horizon-wise Metrics (Regime Hybrid)

### 24h Horizon
- Sample count: 2
- Mean EPE: 2123.5 m
- Median EPE: 2123.5 m
- P95 EPE: 4034.6 m
- MAE: 1428.6 m
- RMSE: 3003.0 m

### 72h Horizon
- Sample count: 25
- Mean EPE: 14427.6 m
- Median EPE: 1522.3 m
- P95 EPE: 76610.9 m
- MAE: 8631.6 m
- RMSE: 29397.7 m

### 168h Horizon
- Sample count: 103
- Mean EPE: 6035.7 m
- Median EPE: 0.0 m
- P95 EPE: 42093.9 m
- MAE: 3664.6 m
- RMSE: 15257.9 m

### 240h Horizon
- Sample count: 86
- Mean EPE: 15613.3 m
- Median EPE: 0.0 m
- P95 EPE: 94307.2 m
- MAE: 10036.6 m
- RMSE: 36774.0 m

### 720h Horizon
- Sample count: 36
- Mean EPE: 27171.6 m
- Median EPE: 3062.1 m
- P95 EPE: 117474.9 m
- MAE: 17630.4 m
- RMSE: 55744.7 m

## 2. Kinematic Regime Breakdown (Regime Hybrid)

### Stationary (<0.01 m/s)
- Sample count: 188
- Mean EPE: 1361.9 m
- Median EPE: 0.0 m
- P95 EPE: 6877.2 m

### Slow-moving (0.01-0.03 m/s)
- Sample count: 21
- Mean EPE: 26888.5 m
- Median EPE: 10471.8 m
- P95 EPE: 99316.9 m

### Moving (>=0.03 m/s)
- Sample count: 43
- Mean EPE: 57833.4 m
- Median EPE: 48850.4 m
- P95 EPE: 125189.6 m

## 3. Model Comparison

### 24h Horizon
- Persistence Mean EPE: 2123.5 m
- Physics B Mean EPE: 2392.8 m
- Regime Hybrid Mean EPE: 2123.5 m


### 72h Horizon
- Persistence Mean EPE: 16027.2 m
- Physics B Mean EPE: 14722.1 m
- Regime Hybrid Mean EPE: 14427.6 m


### 168h Horizon
- Persistence Mean EPE: 8012.1 m
- Physics B Mean EPE: 6964.1 m
- Regime Hybrid Mean EPE: 6035.7 m


### 240h Horizon
- Persistence Mean EPE: 20714.2 m
- Physics B Mean EPE: 16829.4 m
- Regime Hybrid Mean EPE: 15613.3 m


### 720h Horizon
- Persistence Mean EPE: 35974.3 m
- Physics B Mean EPE: 29472.9 m
- Regime Hybrid Mean EPE: 27171.6 m

