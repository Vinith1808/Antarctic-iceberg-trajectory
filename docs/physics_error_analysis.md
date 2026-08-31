# Phase 8.7.1: Physics Baseline Error & Regime Analysis

## 1. Error Correlation Analysis (Spearman Rank)
* **Initial Iceberg Speed**: 0.767
* **Target Time Horizon**: 0.180
* **Ocean Current Speed**: 0.240
* **Wind Speed**: -0.002
* **Sea-Ice Concentration**: -0.037
* **Absolute Latitude**: 0.147
* **Previous Distance Travelled**: 0.759

*Note: These are descriptive test-set correlations intended to identify failure modes, NOT to tune future models.*

## 2. Regime Analysis
| Regime | Count | Mean EPE (m) | Median EPE (m) | P90 EPE (m) | P95 EPE (m) | Mean Pred Disp (m) | Mean Actual Disp (m) |
|---|---|---|---|---|---|---|---|
| Stationary (<0.01 m/s) | 188 | 2762.0 | 1136.4 | 6309.8 | 10433.0 | 1736.1 | 1361.9 |
| Moving (>=0.01 m/s) | 64 | 48113.0 | 35624.0 | 99619.9 | 124866.8 | 41849.6 | 63291.1 |

### Moving Velocity Bins:
| Regime | Count | Mean EPE (m) | Median EPE (m) | P90 EPE (m) | P95 EPE (m) | Mean Pred Disp (m) | Mean Actual Disp (m) |
|---|---|---|---|---|---|---|---|
| 0.01 - 0.03 m/s | 21 | 28209.2 | 15298.5 | 77221.5 | 83961.6 | 10143.7 | 26888.5 |
| 0.03 - 0.10 m/s | 30 | 56430.6 | 48954.9 | 103585.8 | 119671.0 | 45926.3 | 73706.1 |
| 0.10 - 0.30 m/s | 13 | 61070.8 | 42944.4 | 114018.8 | 139513.8 | 83659.1 | 98060.7 |


## 3. Sea-Ice Analysis (Physics Model B)
| SIC Regime | Count | Mean EPE (m) | Median EPE (m) |
|---|---|---|---|
| SIC < 0.2 | 53 | 12968.5 | 2317.8 |
| 0.2 - 0.5 | 8 | 13518.4 | 4005.8 |
| 0.5 - 0.8 | 26 | 13083.4 | 3608.2 |
| SIC >= 0.8 | 165 | 14926.3 | 1824.8 |

## 4. Prediction Bias Analysis
* **Overall Mean Bias**: -5166.3 m (Positive = Overprediction)
* **Overall Median Bias**: 381.4 m
* **Stationary Mean Bias**: 374.2 m
* **Stationary Median Bias**: 481.1 m
* **Moving Mean Bias**: -21441.5 m
* **Moving Median Bias**: -10820.3 m

## 5. Outlier Analysis (Top 20 Errors)
| Iceberg | Target | EPE (km) | Actual Disp (km) | Pred Disp (km) | Init Vel (m/s) | Curr Speed (m/s) | Wind (m/s) | SIC | Horizon (h) |
|---|---|---|---|---|---|---|---|---|---|
| d27 | 2021-08-15 | 213.2 | 200.6 | 61.0 | 0.04 | 0.13 | 16.6 | 0.95 | 720.0 |
| d27 | 2021-05-04 | 169.7 | 243.7 | 149.7 | 0.20 | 0.16 | 16.6 | 0.94 | 312.0 |
| d30b | 2021-11-10 | 161.5 | 162.0 | 29.7 | 0.02 | 0.09 | 10.4 | 0.80 | 528.0 |
| a81 | 2026-08-09 | 125.8 | 156.4 | 34.3 | 0.06 | 0.10 | 9.1 | 0.00 | 240.0 |
| d27 | 2021-06-17 | 119.4 | 171.1 | 71.7 | 0.14 | 0.18 | 2.6 | 0.84 | 216.0 |
| d27 | 2021-04-21 | 112.1 | 156.7 | 49.2 | 0.10 | 0.09 | 5.6 | 0.87 | 216.0 |
| d27 | 2021-10-06 | 102.6 | 162.4 | 59.9 | 0.04 | 0.11 | 4.3 | 0.93 | 576.0 |
| a81 | 2026-07-22 | 92.6 | 72.5 | 34.0 | 0.12 | 0.10 | 2.8 | 0.00 | 120.0 |
| b46 | 2021-10-06 | 88.1 | 149.1 | 114.2 | 0.08 | 0.04 | 3.4 | 0.91 | 576.0 |
| d27 | 2021-04-12 | 84.0 | 99.3 | 19.2 | 0.03 | 0.11 | 4.5 | 0.80 | 288.0 |
| a81 | 2026-07-03 | 81.4 | 86.8 | 27.1 | 0.09 | 0.05 | 12.9 | 0.00 | 120.0 |
| d27 | 2021-10-19 | 79.3 | 131.3 | 58.8 | 0.08 | 0.14 | 9.9 | 0.89 | 312.0 |
| a81 | 2026-06-21 | 77.2 | 78.4 | 10.6 | 0.02 | 0.05 | 3.5 | 0.23 | 192.0 |
| d27 | 2021-11-10 | 72.1 | 216.2 | 147.2 | 0.12 | 0.14 | 10.3 | 0.95 | 528.0 |
| d27 | 2021-06-08 | 70.7 | 131.1 | 60.4 | 0.10 | 0.09 | 8.7 | 0.92 | 264.0 |
| b46 | 2021-07-16 | 70.3 | 77.2 | 46.7 | 0.08 | 0.05 | 4.8 | 0.96 | 240.0 |
| b46 | 2021-11-10 | 68.8 | 84.9 | 49.2 | 0.04 | 0.05 | 2.7 | 0.89 | 528.0 |
| b09b | 2021-05-28 | 65.6 | 0.0 | 65.6 | 0.05 | 0.09 | 0.5 | 0.94 | 552.0 |
| a81 | 2026-08-16 | 63.7 | 14.5 | 71.4 | 0.18 | 0.10 | 9.1 | 0.00 | 168.0 |
| a81 | 2026-07-12 | 60.8 | 61.9 | 106.0 | 0.20 | 0.10 | 11.6 | 0.00 | 216.0 |

## 6. Physics vs Persistence Crossover
| Velocity Bin (m/s) | % where Physics B beats Persistence |
|---|---|
| <0.01 | 9.0% |
| 0.01-0.03 | 52.4% |
| 0.03-0.10 | 76.7% |
| 0.10-0.30 | 76.9% |
| >0.30 | nan% |