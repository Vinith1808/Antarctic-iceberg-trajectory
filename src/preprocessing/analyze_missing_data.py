import pandas as pd
import numpy as np
from pathlib import Path

def generate_missing_analysis():
    df = pd.read_parquet('data/processed/iceberg_modeling.parquet')
    
    # 1. Complete Data Quality Analysis
    total_obs = len(df)
    total_icebergs = df['iceberg_id'].nunique()
    dupes = df.duplicated(subset=['iceberg_id', 'timestamp']).sum()
    
    obs_per_iceberg = df.groupby('iceberg_id').size()
    
    gap_hours = df['time_since_previous_observation_hours'].dropna()
    gap_stats = {
        'min': gap_hours.min(),
        'median': gap_hours.median(),
        'mean': gap_hours.mean(),
        '75th': gap_hours.quantile(0.75),
        '95th': gap_hours.quantile(0.95),
        'max': gap_hours.max()
    }
    
    vel_stats = {
        'min': df['velocity_ms'].min(),
        'median': df['velocity_ms'].median(),
        'mean': df['velocity_ms'].mean(),
        'max': df['velocity_ms'].max()
    }
    
    # Missing environmental data
    env_vars = ['uo', 'vo', 'current_speed_ms', 'current_direction_deg', 
                'u10', 'v10', 'wind_speed_ms', 'wind_direction_deg', 'siconc']
    
    missing_report = []
    for var in env_vars:
        missing_count = df[var].isna().sum()
        pct = (missing_count / total_obs) * 100
        missing_report.append(f"- **{var}**: {missing_count} missing ({pct:.2f}%)")
        
    # Analyze by quality flags
    current_flags = df['current_quality_flag'].value_counts()
    wind_flags = df['wind_quality_flag'].value_counts()
    seaice_flags = df['seaice_quality_flag'].value_counts()
    
    missing_report_str = "".join([f"{x}\n" for x in missing_report])
    
    # Markdown Generation
    md = f"""# Phase 8.2: Missing Data & Data Quality Analysis

## 1. General Statistics
* **Observations:** {total_obs}
* **Unique Icebergs:** {total_icebergs}
* **Duplicates:** {dupes}
* **Observations per Iceberg:** Min: {obs_per_iceberg.min()}, Median: {obs_per_iceberg.median()}, Max: {obs_per_iceberg.max()}

## 2. Temporal Gaps (`time_since_previous_observation_hours`)
* **Min:** {gap_stats['min']:.2f} hours
* **Median:** {gap_stats['median']:.2f} hours
* **Mean:** {gap_stats['mean']:.2f} hours
* **75th Percentile:** {gap_stats['75th']:.2f} hours
* **95th Percentile:** {gap_stats['95th']:.2f} hours
* **Max:** {gap_stats['max']:.2f} hours

*Note on Sequence Modeling:* The max gap of {gap_stats['max']:.2f} hours (approx {gap_stats['max']/24:.1f} days) is an extreme outlier. Standard LSTM models assume uniform time steps. The 95th percentile ({gap_stats['95th']:.2f}h) shows most data is sampled at roughly daily to bi-daily intervals. We will need to either encode `time_since_previous_observation_hours` as an explicit input feature (time-aware LSTM/Transformer) or resample trajectories.

## 3. Velocity Distribution
* **Min:** {vel_stats['min']:.4f} m/s
* **Median:** {vel_stats['median']:.4f} m/s
* **Mean:** {vel_stats['mean']:.4f} m/s
* **Max:** {vel_stats['max']:.4f} m/s

## 4. Missing Environmental Data
{missing_report_str}

### Missingness Causes (via Quality Flags)
**Ocean Currents:**
{current_flags.to_string()}

**Wind (ERA5):**
{wind_flags.to_string()}

**Sea Ice (CMEMS):**
{seaice_flags.to_string()}

*Analysis:* 
- Missingness in Sea Ice is predominantly caused by `OUTSIDE_COVERAGE` (dates > 2026-06-23).
- Missingness in currents/wind is largely due to spatial coverage/landmask proximity or minor API failures.

## 5. Interpolation Strategy Recommendation
**Recommendation: E. Retain NaN and use availability masks.**

*Reasoning:* 
1. The environmental parameters (wind, current, ice) change rapidly. Forward filling or interpolating over large temporal gaps (e.g., >48 hours) will introduce massive physical inaccuracies (e.g. hallucinating a storm that has passed).
2. We cannot safely interpolate sea ice for dates beyond `2026-06-23` (OUTSIDE_COVERAGE), as this would project past dataset validity.
3. Neural networks (especially transformers or masked LSTMs) can natively handle missing values if provided with the availability indicators (`current_available`, `wind_available`, `seaice_available`) which we have already created.
4. We can use 0 for missing values *only after splitting*, as long as the availability mask is explicitly provided to the model.

If we *must* interpolate for a standard LSTM, we recommend **D. Limited interpolation (max gap = 24 hours)** followed by masking. For now, we will leave them as NaN in the split files to prevent silent leakage.
"""
    with open('docs/missing_data_analysis.md', 'w') as f:
        f.write(md)
    print("Generated missing_data_analysis.md")

if __name__ == '__main__':
    generate_missing_analysis()
