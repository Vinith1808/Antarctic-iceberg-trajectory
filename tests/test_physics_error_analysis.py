import pytest
import pandas as pd
import numpy as np
from pathlib import Path

def test_physics_error_analysis_output():
    # Since we can't easily mock the entire pipeline in a unit test without duplicating it,
    # we test the properties of the output dataframe.
    csv_path = Path('docs/physics_error_analysis.csv')
    if not csv_path.exists():
        pytest.skip("physics_error_analysis.csv not generated yet")
        
    df = pd.read_csv(csv_path)
    
    # Check all test sequences preserved
    test_meta = pd.read_parquet('data/processed/sequences/test_meta.parquet')
    assert len(df) == len(test_meta), "Number of sequences should match test set"
    
    # Check no duplicate IDs? (Wait, an iceberg can have multiple sequences. So we check if the len matches)
    assert len(df) == 252 # Based on previous known size
    
    # EPE calculations correct
    recalc_epe = np.sqrt((df['physics_dx'] - df['actual_dx'])**2 + (df['physics_dy'] - df['actual_dy'])**2)
    assert np.allclose(df['physics_epe'], recalc_epe), "Physics EPE math incorrect"
    
    # Displacement magnitude correct
    recalc_pred_mag = np.sqrt(df['physics_dx']**2 + df['physics_dy']**2)
    assert np.allclose(df['predicted_displacement_magnitude'], recalc_pred_mag), "Pred mag incorrect"
    
    # Check no unexpected NaNs (except possibly where delta_t is weird or velocity is 0)
    assert not df['physics_epe'].isna().any(), "NaNs in EPE"
