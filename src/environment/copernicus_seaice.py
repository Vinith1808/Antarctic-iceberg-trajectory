import os
import argparse
import pandas as pd
import numpy as np
import copernicusmarine
from pathlib import Path
import xarray as xr
from dotenv import load_dotenv

# Setup env
load_dotenv()

DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
VARIABLES = ["siconc"]
SPATIAL_MARGIN = 0.5  # degrees
DATASET_END_DATE = pd.to_datetime('2026-06-23 00:00:00')

def get_active_months(df):
    """Group observations by active month to create manageable download chunks."""
    valid = df[df['motion_quality_flag'] != 'ANOMALOUS_VELOCITY'].copy()
    valid['year_month'] = valid['timestamp'].dt.to_period('M')
    
    chunks = []
    for ym, group in valid.groupby('year_month'):
        chunk = {
            'year_month': str(ym),
            'min_time': group['timestamp'].min() - pd.Timedelta(days=1),
            'max_time': group['timestamp'].max() + pd.Timedelta(days=1),
            'min_lat': max(-90.0, group['latitude'].min() - SPATIAL_MARGIN),
            'max_lat': min(90.0, group['latitude'].max() + SPATIAL_MARGIN),
            'min_lon': group['longitude'].min() - SPATIAL_MARGIN,
            'max_lon': group['longitude'].max() + SPATIAL_MARGIN,
            'obs_count': len(group),
            'observations': group
        }
        
        if chunk['min_lon'] < -180: chunk['min_lon'] = -180.0
        if chunk['max_lon'] > 180: chunk['max_lon'] = 180.0
            
        chunks.append(chunk)
    return chunks

def download_chunk(chunk, out_dir):
    out_file = out_dir / f"seaice_{chunk['year_month']}.nc"
    if out_file.exists():
        return out_file
        
    print(f"Downloading {out_file.name}...")
    
    username = os.getenv('COPERNICUSMARINE_USERNAME')
    password = os.getenv('COPERNICUSMARINE_PASSWORD')
    if not username or not password:
        raise ValueError("Missing Copernicus Marine credentials for real download.")

    # Limit max time to dataset availability to avoid API errors
    req_max_time = min(chunk['max_time'], DATASET_END_DATE)
    req_min_time = min(chunk['min_time'], DATASET_END_DATE)
    
    if req_min_time == DATASET_END_DATE and chunk['min_time'] > DATASET_END_DATE:
        print(f"Chunk {chunk['year_month']} is entirely outside dataset coverage.")
        return None # Return None to indicate no file
        
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            copernicusmarine.subset(
                dataset_id=DATASET_ID,
                variables=VARIABLES,
                minimum_longitude=chunk['min_lon'],
                maximum_longitude=chunk['max_lon'],
                minimum_latitude=chunk['min_lat'],
                maximum_latitude=chunk['max_lat'],
                start_datetime=req_min_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_datetime=req_max_time.strftime('%Y-%m-%d %H:%M:%S'),
                output_filename=out_file.name,
                output_directory=str(out_dir),
                force_download=True,
                username=username,
                password=password
            )
            break
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt * 10
                print(f"Failed chunk {chunk['year_month']}, retrying in {sleep_time}s... Error: {e}")
                time.sleep(sleep_time)
            else:
                print(f"Failed chunk {chunk['year_month']} after {max_retries} attempts. Error: {e}")
                return None
    return out_file

def extract_points(chunk_file, observations):
    results = []
    
    ds = None
    if chunk_file and chunk_file.exists():
        try:
            ds = xr.open_dataset(chunk_file)
        except Exception as e:
            print(f"Failed to open NetCDF {chunk_file}: {e}")
            ds = None
            
    for _, row in observations.iterrows():
        result = {
            'iceberg_id': row['iceberg_id'],
            'timestamp': row['timestamp'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'siconc': np.nan,
            'cmems_timestamp': pd.NaT,
            'cmems_latitude': np.nan,
            'cmems_longitude': np.nan,
            'seaice_quality_flag': 'VALID'
        }
        
        if row['timestamp'] > DATASET_END_DATE:
            result['seaice_quality_flag'] = 'OUTSIDE_COVERAGE'
            results.append(result)
            continue
            
        if ds is None:
            result['seaice_quality_flag'] = 'MISSING_SIC'
            results.append(result)
            continue
            
        try:
            point_data = ds.sel(
                longitude=row['longitude'],
                latitude=row['latitude'],
                time=row['timestamp'],
                method='nearest'
            )
            
            siconc = float(point_data['siconc'].values)
            c_time = pd.to_datetime(point_data['time'].values)
            c_lat = float(point_data['latitude'].values)
            c_lon = float(point_data['longitude'].values)
            
            result['cmems_timestamp'] = c_time
            result['cmems_latitude'] = c_lat
            result['cmems_longitude'] = c_lon
            
            if np.isnan(siconc):
                result['siconc'] = np.nan
                result['seaice_quality_flag'] = 'MISSING_SIC'
            else:
                result['siconc'] = siconc
                
                time_diff_hours = abs((row['timestamp'] - c_time).total_seconds()) / 3600.0
                if time_diff_hours > 24:
                    result['seaice_quality_flag'] = 'TEMPORAL_MISMATCH'
                elif abs(row['latitude'] - c_lat) > 0.1 or abs(row['longitude'] - c_lon) > 0.1:
                    result['seaice_quality_flag'] = 'SPATIAL_MISMATCH'
                    
        except KeyError:
            result['seaice_quality_flag'] = 'OUTSIDE_COVERAGE'
        except Exception as e:
            result['seaice_quality_flag'] = 'MISSING_SIC'
            
        results.append(result)
            
    if ds is not None:
        ds.close()
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-download', action='store_true')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    
    if not (args.test_download or args.download):
        print("Please specify --test-download or --download")
        return
        
    df = pd.read_parquet('data/processed/iceberg_motion.parquet')
    
    if args.test_download:
        df_early = df[df['timestamp'] < pd.to_datetime('2026-06-01')].head(8)
        df_late = df[df['timestamp'] > pd.to_datetime('2026-07-01')].head(2)
        target_df = pd.concat([df_early, df_late]).copy()
        out_dir = Path('data/test/copernicus_seaice')
        out_parquet = out_dir / 'iceberg_seaice_test.parquet'
    else:
        target_df = df.copy()
        out_dir = Path('data/raw/environment/seaice')
        out_parquet = Path('data/processed/iceberg_seaice.parquet')
        
    out_dir.mkdir(parents=True, exist_ok=True)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    
    chunks = get_active_months(target_df)
    
    all_results = []
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {
            executor.submit(download_chunk, chunk, out_dir): chunk 
            for chunk in chunks
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
            chunk = future_to_chunk[future]
            try:
                nc_file = future.result()
                if nc_file:
                    print(f"[{i+1}/{len(chunks)}] Downloaded chunk {chunk['year_month']}")
                else:
                    print(f"[{i+1}/{len(chunks)}] Chunk {chunk['year_month']} has no data.")
                res_df = extract_points(nc_file, chunk['observations'])
                all_results.append(res_df)
            except Exception as e:
                print(f"[{i+1}/{len(chunks)}] Failed chunk {chunk['year_month']}: {e}")
                failed_results = []
                for _, row in chunk['observations'].iterrows():
                    failed_results.append({
                        'iceberg_id': row['iceberg_id'],
                        'timestamp': row['timestamp'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'siconc': np.nan,
                        'cmems_timestamp': pd.NaT,
                        'cmems_latitude': np.nan,
                        'cmems_longitude': np.nan,
                        'seaice_quality_flag': 'MISSING_SIC'
                    })
                all_results.append(pd.DataFrame(failed_results))
                
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        # Ensure row counts match (we processed every row in chunks)
        if len(final_df) != len(target_df):
            # This shouldn't happen unless anomalous records were filtered out, so append anomalous back.
            anomalous = df[df['motion_quality_flag'] == 'ANOMALOUS_VELOCITY'].copy()
            if not anomalous.empty and args.download:
                ano_res = []
                for _, row in anomalous.iterrows():
                    ano_res.append({
                        'iceberg_id': row['iceberg_id'],
                        'timestamp': row['timestamp'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'siconc': np.nan,
                        'cmems_timestamp': pd.NaT,
                        'cmems_latitude': np.nan,
                        'cmems_longitude': np.nan,
                        'seaice_quality_flag': 'OUTSIDE_COVERAGE'
                    })
                final_df = pd.concat([final_df, pd.DataFrame(ano_res)], ignore_index=True)
                
        final_df = final_df.sort_values(['iceberg_id', 'timestamp'])
        final_df.to_parquet(out_parquet, index=False)
        print(f"\nExtraction complete. Rows: {len(final_df)}. Results saved to {out_parquet}")
        
if __name__ == '__main__':
    main()
