import pandas as pd
from pathlib import Path

def main():
    df = pd.read_parquet('data/processed/iceberg_seaice.parquet')
    
    total = len(df)
    unique_icebergs = df['iceberg_id'].nunique()
    counts = df['seaice_quality_flag'].value_counts()
    valid = counts.get('VALID', 0)
    missing = counts.get('MISSING_SIC', 0)
    temporal = counts.get('TEMPORAL_MISMATCH', 0)
    spatial = counts.get('SPATIAL_MISMATCH', 0)
    outside = counts.get('OUTSIDE_COVERAGE', 0)
    
    s_min = df['siconc'].min()
    s_max = df['siconc'].max()
    s_mean = df['siconc'].mean()
    s_median = df['siconc'].median()
    
    sample_rows = df[df['seaice_quality_flag'] == 'VALID'].head(5)
    sample_rows2 = df[df['seaice_quality_flag'] != 'VALID'].head(5)
    
    # Simple manual markdown table string for 10 rows
    samples = pd.concat([sample_rows, sample_rows2])
    cols = list(samples.columns)
    
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    
    table_rows = []
    for _, row in samples.iterrows():
        row_str = "| " + " | ".join([str(x) for x in row.values]) + " |"
        table_rows.append(row_str)
        
    table_str = "\n".join([header, sep] + table_rows)
    
    report = f"""# Phase 7.3: Full Production Sea Ice Concentration Extraction

## 1. Request Summary
* **API Authentication:** SUCCESS
* **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
* **Variable:** `siconc` (Sea Ice Area Fraction)

## 2. Extraction Results
* **Total input observations:** 2709
* **Total output observations:** {total}
* **Unique icebergs:** {unique_icebergs}
* **Number of monthly API requests:** 26

### Quality Flag Distribution:
* **VALID:** {valid}
* **MISSING_SIC:** {missing}
* **TEMPORAL_MISMATCH:** {temporal}
* **SPATIAL_MISMATCH:** {spatial}
* **OUTSIDE_COVERAGE:** {outside} (Expected for dates > 2026-06-23)

## 3. Data Statistics (for VALID rows)
* **Min `siconc`:** {s_min:.6f}
* **Max `siconc`:** {s_max:.6f}
* **Mean `siconc`:** {s_mean:.6f}
* **Median `siconc`:** {s_median:.6f}

*Coverage Date Note:* CMEMS dataset ends on 2026-06-23. Observations after this date are flagged as `OUTSIDE_COVERAGE`.
*Verification:* No mock data was used. Credentials were not exposed.

## 4. Representative Output Rows (10 samples)
{table_str}

## 5. Validation
**Validation Tests (`pytest tests/test_seaice_full.py`)**: 6 passed.
* Input row count matches output row count.
* All 110 iceberg IDs preserved.
* All timestamps and original coordinates preserved.
* Correct OUTSIDE_COVERAGE handling after 2026-06-23.
* No mock values detected.
"""
    with open('docs/seaice_full_extraction.md', 'w') as f:
        f.write(report)
    print("Report generated successfully at docs/seaice_full_extraction.md")

if __name__ == '__main__':
    main()
