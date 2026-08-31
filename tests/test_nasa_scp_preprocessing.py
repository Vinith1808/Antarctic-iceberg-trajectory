import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add src to path to import the function
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.preprocessing.preprocess_nasa_scp import convert_dms

def test_convert_dms():
    # Regular coordinates
    assert convert_dms("75 45'S") == -75.75
    assert convert_dms("40 0'W") == -40.0
    assert convert_dms("66 14'S") == -(66 + 14/60)
    assert convert_dms("143 22'E") == 143 + 22/60
    assert convert_dms("68 0'S") == -68.0
    
    # Missing degrees (e.g. 0'N or 0'E)
    assert convert_dms("0'N") == 0.0
    assert convert_dms("0'E") == 0.0
    assert convert_dms("15'W") == -15/60
    
    # Nulls
    assert np.isnan(convert_dms(np.nan))
    assert np.isnan(convert_dms(None))
    assert np.isnan(convert_dms("invalid string"))

def test_dataframe_sorting_and_gaps():
    # Mock data to test calculations in step 9 and 10
    import pandas as pd
    
    data = {
        'iceberg_id': ['a1', 'a1', 'a1', 'b1', 'b1'],
        'timestamp': pd.to_datetime(['2021-01-01', '2021-01-03', '2021-01-02', '2021-02-01', '2021-02-01'])
    }
    df = pd.DataFrame(data)
    
    # Sort
    df = df.sort_values(by=['iceberg_id', 'timestamp']).reset_index(drop=True)
    
    assert df.loc[1, 'timestamp'] == pd.to_datetime('2021-01-02')
    
    df['observation_index'] = df.groupby('iceberg_id').cumcount()
    df['time_since_previous_observation_hours'] = df.groupby('iceberg_id')['timestamp'].diff().dt.total_seconds() / 3600.0
    
    assert df.loc[1, 'observation_index'] == 1
    assert df.loc[1, 'time_since_previous_observation_hours'] == 24.0
    assert df.loc[2, 'time_since_previous_observation_hours'] == 24.0
    assert pd.isna(df.loc[0, 'time_since_previous_observation_hours'])

