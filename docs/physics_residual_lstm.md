# Phase 8.6.2: Physics-Informed Residual LSTM

## 1. Motivation
The Vanilla LSTM natively struggles to parse the chaotic mapping between highly auto-correlated sequential covariates and physical target displacements. Phase 8.6.1 successfully demonstrated that a very naive, deterministic linear combination of physical vectors (Ocean + Wind + Iceberg Velocity) drastically outperforms the Vanilla LSTM, particularly on moving icebergs. The objective of this phase is to evaluate whether a "Physics-Informed Residual LSTM" can leverage the predictive stability of the Physics model while deploying deep learning specifically to correct its residuals (the non-linear fluid drag or unaccounted dynamics).

## 2. Mathematical Formulation
* **Base Physics Model**: The network inherits the predictions of Physics Model B (Sea-Ice Modulated) as an explicit prior.
* **Residual Target Formulation**: 
  * $residual\_dx = target\_dx - physics\_dx$
  * $residual\_dy = target\_dy - physics\_dy$
* **Prediction Formulation**: 
  * $predicted\_dx = physics\_dx + predicted\_residual\_dx$
  * $predicted\_dy = physics\_dy + predicted\_residual\_dy$

## 3. Architecture & Leakage Prevention
* **Architecture**: The sequence of 22 environmental/motion features (`[batch, 10, 22]`) is processed through a standard 2-layer LSTM (Hidden Size: 128, Dropout: 0.2). The final hidden representation is explicitly concatenated with the pre-scaled $physics\_dx, physics\_dy$ predictions. This merged vector feeds a Dense Layer mapping to the scaled $residual\_dx, residual\_dy$.
* **Leakage Integrity**: The Physics Base Model was isolated entirely to the Training Set. The Residual Target Scaler (`StandardScaler`) was fitted purely on the Training Subsets' residuals. The Test and Validation sets were evaluated immutably via inverse transformations.

## 4. Ablation Study & Training Procedure
An ablation study on the validation subset confirmed whether Physics Model A or Physics Model B (Sea-Ice modulated) provided a better prior for residual learning.
* **Variant B (Physics A prior)**: Validation Real MAE = 13,440 m
* **Variant C (Physics B prior)**: Validation Real MAE = 13,171 m
Variant C (incorporating sea-ice physics) was structurally confirmed as the superior architecture and advanced to Test Evaluation.

## 5. Test Evaluation Results

### Overall Mean Endpoint Error (EPE)
1. **Physics Model B:** 14,279 m
2. **Constant Velocity:** 15,101 m
3. **Physics Model A:** 15,855 m
4. **Persistence:** 17,090 m
5. **Vanilla LSTM:** 19,234 m
6. **Physics + Residual LSTM:** 19,535 m

### Breakdowns by Kinematic State
* **Stationary Icebergs (< 0.01 m/s):**
  * Persistence: 1,361 m
  * Physics B: 2,762 m
  * **Vanilla LSTM:** 7,802 m
  * **Physics + Residual LSTM:** 8,487 m
* **Moving Icebergs (>= 0.01 m/s):**
  * Physics B: 48,113 m
  * **Physics + Residual LSTM:** 51,990 m
  * Vanilla LSTM: 52,813 m
  * Constant Velocity: 53,901 m
  * Persistence: 63,291 m

## 6. Stationary Analysis
Physics Model B successfully anchors stationary predictions (Mean EPE: 2.7km) because iceberg momentum limits to 0, restricting motion. However, the neural network actively overrides this anchor.
* **Mean Predicted Displacement (Residual LSTM):** 7,817 m (vs 1,736 m for Physics B).
* **% of Stationary cases moved > 1km:** 93.62%
* **% of Stationary cases moved > 5km:** 35.11%
The residual model hallucinates significant movement when the iceberg is empirically grounded. 

## 7. Limitations & Conclusion
The Physics + Residual LSTM essentially collapses back to the performance ceiling of the Vanilla LSTM (-1.57% "improvement" vs Vanilla). Rather than strictly learning minor residual corrections to the physical baseline, the network aggressively overwrites the physical prior, manifesting the exact same vulnerabilities (hallucinated motion, overfitting sequential noise) as the unconstrained Vanilla version. It performed worse than the deterministic Physics Model B by **-36.8%**. Future models must either rigidly hardcode grounding overrides, or move towards massive Transformer architectures capable of interpreting spatial interactions rather than isolated time-series sequences.
