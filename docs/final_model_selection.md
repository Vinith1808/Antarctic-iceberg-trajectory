# Phase 8.8: Final Model Selection & Ablation

## 1. Objective
The goal of this phase is to finalize the deployment candidate for the Antarctic Iceberg Trajectory Prediction system, ensuring the selected model possesses the optimal balance of accuracy, physical interpretability, and robustness to missing environmental data.

## 2. All Candidate Models & Final Test Performance
The following models were developed, tuned appropriately, and evaluated on the final, completely withheld Test Set consisting of 252 iceberg sequence trajectories.

| Model | Test-Set Mean EPE | Description |
|:---|---:|:---|
| **Regime Hybrid Predictor** | **13.125 km** | Dynamic thresholding between Persistence and Physics B |
| **Physics Model B** | 14.280 km | Fluid dynamics equation + Sea-Ice momentum dampening |
| Constant Velocity | 15.101 km | Purely inertial model |
| Physics Model A | 15.855 km | Fluid dynamics equation without Sea-Ice |
| **Persistence** | 17.090 km | 0 km displacement prediction (iceberg remains stationary) |
| Vanilla LSTM | 19.234 km | Deep learning temporal sequence model |
| Physics + Residual LSTM | 19.535 km | LSTM predicting errors on top of Physics Model B |

## 3. Ablation Comparison
To definitively prove the necessity of the hybrid decision policy, we ablate the system to rely strictly on one of its underlying models universally across all kinematic states. 

* **What happens if Persistence is used everywhere?**
  * Error inflates to **17.090 km**. 
  * The system becomes exceptionally accurate at tracking grounded icebergs, but fails catastrophically (63+ km mean errors) when icebergs break free and begin actively drifting.
  
* **What happens if Physics B is used everywhere?**
  * Error inflates to **14.280 km**.
  * The physical fluid equations reliably trace fast-moving icebergs, but hallucinate false drift (2.7 km mean errors) for icebergs that are empirically stationary or grounded in dense sea-ice pack.
  
* **What happens when the regime policy selects between them?**
  * Error drops to **13.125 km**.
  * By routing icebergs with initial velocities $< 0.03$ m/s to the Persistence model and $\ge 0.03$ m/s to the Physics B model, the system avoids both the catastrophic active-drift errors of Persistence and the hallucinated drift errors of the Physics model.

## 4. Why Regime Hybrid Was Selected
> **The Regime-Aware Hybrid Predictor is the selected deployment model because it achieved the lowest observed Mean Endpoint Error while remaining lightweight, interpretable, and robust to missing environmental covariates.**

Deep learning architectures (Vanilla LSTM, Residual LSTM) exhibited persistent overfitting to temporal noise and actively corrupted physical invariants. The Regime Hybrid sidesteps neural network hallucination by deploying deterministic, validated algorithms optimally matched to the empirically observed iceberg state.

## 5. Final Decision Rule
The deployment policy utilizes a strict threshold discovered during the Validation phase:

* **Threshold:** $0.03$ m/s
* **Low-Speed Regime Model:** Persistence (0 displacement)
* **High-Speed Regime Model:** Physics Model B
* **Missing Data Fallback:** If the required variables (iceberg velocity, ocean currents, wind, etc.) are entirely missing, the system gracefully falls back to Persistence.

## 6. Known Limitations
1. **Hard Thresholding:** The $0.03$ m/s boundary is rigid; an iceberg at $0.029$ m/s receives a different mathematical treatment than one at $0.031$ m/s.
2. **Missing Preemptive Logic:** The model routes based strictly on the iceberg's *previous* velocity. It cannot preemptively predict when a currently grounded iceberg will break free until after it has started moving.
3. **High-Speed Bias:** As velocities scale upwards (> $0.3$ m/s), Physics Model B systematically underestimates total drift magnitude, suggesting unmodeled non-linear forces (e.g. extreme winds or wave action) are unaccounted for.

## 7. Deployment Recommendation
The `RegimeHybridPredictor` (exposed in `src/modeling/regime_hybrid.py`) is fully configured via `config/trajectory_model.yaml` and is ready for production deployment. It should be invoked with the standard `predict_trajectory()` interface to guarantee non-destructive coordinate preservation and edge-case safety.
