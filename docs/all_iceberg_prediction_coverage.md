# All-Iceberg Trajectory Prediction Coverage

## Dataset Summary
- **Total observations**: 2709
- **Unique iceberg IDs**: 110
- **Time range**: 2020-12-31 00:00:00 to 2026-08-16 00:00:00
- **Expected predictions**: 550 (110 icebergs × 5 horizons)

## Validation Results

| Metric                          | Result |
| ------------------------------- | ------ |
| Total iceberg IDs               | 110 |
| Icebergs successfully predicted | 110 |
| Icebergs failed                 | 0 |
| Total predictions               | 550 |
| Expected predictions            | 550 |
| NaN predictions                 | 0 |
| Infinite predictions            | 0 |
| Persistence                     | 305 |
| Physics B                       | 170 |
| Persistence fallback            | 75 |
| Missing environmental data      | 24 |

All 110 icebergs were successfully processed using the frozen Regime-Aware Hybrid Predictor. Fallback logic safely handled the 24 icebergs with missing environmental data.
