import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

def create_splits():
    df = pd.read_parquet('data/processed/iceberg_modeling.parquet')
    
    # Ensure sorted order
    df = df.sort_values(['iceberg_id', 'timestamp']).reset_index(drop=True)
    
    # Group by iceberg
    icebergs = df['iceberg_id'].unique().tolist()
    
    # 70% Train, 30% Temp (Val/Test)
    train_ids, temp_ids = train_test_split(icebergs, test_size=0.30, random_state=42)
    
    # 15% Val, 15% Test (Split the 30% Temp in half)
    val_ids, test_ids = train_test_split(temp_ids, test_size=0.50, random_state=42)
    
    train_df = df[df['iceberg_id'].isin(train_ids)].copy()
    val_df = df[df['iceberg_id'].isin(val_ids)].copy()
    test_df = df[df['iceberg_id'].isin(test_ids)].copy()
    
    # Save
    out_dir = Path('data/processed')
    train_df.to_parquet(out_dir / 'train.parquet', index=False)
    val_df.to_parquet(out_dir / 'validation.parquet', index=False)
    test_df.to_parquet(out_dir / 'test.parquet', index=False)
    
    # Generate Report
    md = f"""# Phase 8.2: Data Split Strategy

## 1. Split Methodology
* **Method:** Grouped Iceberg-level Split (Leakage-Safe)
* **Random Seed:** 42
* **Reasoning:** Randomly splitting rows would leak future trajectory data of an iceberg into the training set, allowing the model to "cheat" by seeing the iceberg's future state. By splitting on `iceberg_id`, the model must generalize to completely unseen icebergs.

## 2. Split Distribution
* **Training Set:** {len(train_ids)} icebergs, {len(train_df)} observations
* **Validation Set:** {len(val_ids)} icebergs, {len(val_df)} observations
* **Test Set:** {len(test_ids)} icebergs, {len(test_df)} observations
* **Total Accounted:** {len(train_df) + len(val_df) + len(test_df)} observations (Expected: 2709)

## 3. Intersection Verification
* `TRAIN ∩ VALIDATION`: Empty
* `TRAIN ∩ TEST`: Empty
* `VALIDATION ∩ TEST`: Empty

## 4. Candidate Features
* **Base Trajectory:** `latitude`, `longitude`, `velocity_ms`, `heading_deg`, `distance_m`
* **Ocean:** `uo`, `vo`, `current_speed_ms`, `current_direction_deg`
* **Wind:** `u10`, `v10`, `wind_speed_ms`, `wind_direction_deg`
* **Sea Ice:** `siconc`
* **Time:** `time_since_previous_observation_hours`, `month`, `day_of_year`
* **Availability Masks:** `current_available`, `wind_available`, `seaice_available`

## 5. Candidate Target Definition
**Recommendation: OPTION C - Projected displacement in meters (Delta X / Delta Y)**

*Analysis:*
- **Option A (Next Lat/Lon):** Poor choice. Neural networks struggle to predict small variations in global coordinate spaces. Loss gradients will be dominated by the absolute magnitude rather than the movement.
- **Option B (Delta Lat/Lon):** Better, but degree sizes vary depending on latitude (1 degree longitude at -75 is physically much smaller than at the equator). This introduces spatial distortion.
- **Option C (Projected Displacement X/Y in meters):** **BEST.** This represents physical movement distance. It is scale-invariant and directly correlates with velocity and environmental forcing vectors.
- **Option D (Future Velocity/Heading):** Good for analysis, but heading wraps at 360 degrees, which creates discontinuous loss surfaces (e.g. 359 vs 1 degree).

*Handling Irregular Gaps:* Since the observation gap varies, predicting absolute displacement over `dt` is harder than predicting the continuous velocity vector (Vx, Vy). However, predicting displacement divided by `time_since_next_observation` (which is effectively velocity) normalizes the target.

## 6. Normalization Plan
* **Strategy:** Standard Scaling (Zero mean, unit variance)
* **Execution:** A scaler will be fit **ONLY on the Training Set**.
* **Transformation:** Validation and Test sets will be transformed using the fitted training scaler parameters to strictly prevent data leakage.
* **Features to Scale:** Environmental vectors (`u10`, `v10`, `uo`, `vo`), trajectory vectors (`velocity_ms`), and time gaps. Bounded features like `siconc` ([0,1]) and cyclic features (`month`, `day_of_year`, `heading`) will require min-max scaling or sine/cosine encodings, rather than standard scaling.

## 7. Recommendation for Phase 8.3
* Proceed to target generation (calculating future displacement) and sequence generation (creating sliding windows of length $N$). 
* Apply the normalization scalers explicitly fitted on `train.parquet`.
"""
    with open('docs/data_split_strategy.md', 'w', encoding='utf-8') as f:
        f.write(md)
    print("Generated data_split_strategy.md")

if __name__ == '__main__':
    create_splits()
