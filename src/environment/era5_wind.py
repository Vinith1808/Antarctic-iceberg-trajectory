import argparse
import pandas as pd
import numpy as np
import xarray as xr
import yaml
from pathlib import Path
import os
import cdsapi
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore", category=UserWarning) # Ignore xarray warnings if any

def load_config():
    with open('config/era5.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_credentials():
    env_path = Path('.env')
    url = None
    key = None
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('CDSAPI_URL='):
                    url = line.split('=', 1)[1].strip('"\'')
                elif line.startswith('CDSAPI_KEY='):
                    key = line.split('=', 1)[1].strip('"\'')
    return url, key

def get_active_months(df, margin):
    df['year_month'] = df['timestamp'].dt.to_period('M').astype(str)
    chunks = []
    
    for ym, group in df.groupby('year_month'):
        min_lat = group['latitude'].min()
        max_lat = group['latitude'].max()
        min_lon = group['longitude'].min()
        max_lon = group['longitude'].max()
        
        # CDS bounding box: North, West, South, East
        # Latitude is North to South (max to min)
        # Handle wrap around if min_lon is near -180 and max_lon near 180?
        # For simplicity since this is regional, we just use the naive box.
        # If it spans the whole continent, it spans it. 
        N = min(90.0, max_lat + margin)
        S = max(-90.0, min_lat - margin)
        W = max(-180.0, min_lon - margin)
        E = min(180.0, max_lon + margin)
        
        # Ensure we don't have W > E unless wrapping
        if W > E: 
            W = -180.0
            E = 180.0
            
        chunks.append({
            'year_month': ym,
            'observations': group,
            'N': N, 'S': S, 'W': W, 'E': E,
            'year': group['timestamp'].dt.year.iloc[0],
            'month': group['timestamp'].dt.month.iloc[0]
        })
    return chunks

def extract_points(nc_path, observations, config):
    try:
        ds = xr.open_dataset(nc_path)
    except Exception as e:
        print(f"Failed to open {nc_path}: {e}")
        raise e
        
    if 'valid_time' in ds.dims:
        ds = ds.rename({'valid_time': 'time'})
        
    ds = ds.sortby('latitude') # Ensure monotonic
    ds = ds.sortby('longitude')
    
    results = []
    
    max_minutes = config['max_temporal_mismatch_minutes']
    
    for _, row in observations.iterrows():
        ts = row['timestamp']
        lat = row['latitude']
        lon = row['longitude']
        
        # Calculate nearest hour
        target_time = ts.round('h')
        time_diff = abs((ts - target_time).total_seconds() / 60.0)
        
        qf = 'VALID'
        if time_diff > max_minutes:
            qf = 'TEMPORAL_MISMATCH'
            
        # Select spatial
        try:
            pt = ds.sel(latitude=lat, longitude=lon, method='nearest')
            
            # Select temporal
            pt_time = pt.sel(time=target_time, method='nearest')
            
            era5_ts = pd.Timestamp(pt_time.time.values)
            actual_time_diff = abs((ts - era5_ts).total_seconds() / 60.0)
            
            if actual_time_diff > max_minutes and qf == 'VALID':
                 qf = 'TEMPORAL_MISMATCH'
                 
            era5_lat = float(pt_time.latitude.values)
            era5_lon = float(pt_time.longitude.values)
            
            u10 = float(pt_time.u10.values)
            v10 = float(pt_time.v10.values)
            
            if np.isnan(u10) or np.isnan(v10):
                qf = 'MISSING_WIND'
                speed = np.nan
                direction = np.nan
            else:
                speed = np.sqrt(u10**2 + v10**2)
                direction = np.degrees(np.arctan2(u10, v10)) % 360
                
        except Exception as e:
            print(f"DEBUG Exception for {row['iceberg_id']} at {ts}: {e}")
            qf = 'OUTSIDE_COVERAGE'
            u10, v10, speed, direction = np.nan, np.nan, np.nan, np.nan
            era5_ts, era5_lat, era5_lon = pd.NaT, np.nan, np.nan
            
        results.append({
            'iceberg_id': row['iceberg_id'],
            'timestamp': row['timestamp'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'u10': u10 if qf == 'VALID' else np.nan,
            'v10': v10 if qf == 'VALID' else np.nan,
            'wind_speed_ms': speed if qf == 'VALID' else np.nan,
            'wind_direction_deg': direction if qf == 'VALID' else np.nan,
            'era5_timestamp': era5_ts,
            'era5_latitude': era5_lat,
            'era5_longitude': era5_lon,
            'wind_quality_flag': qf
        })
    ds.close()
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--test-download', action='store_true')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    
    config = load_config()
    in_parquet = Path('data/processed/iceberg_motion.parquet')
    
    if not in_parquet.exists():
        print(f"Error: {in_parquet} not found.")
        return
        
    df = pd.read_parquet(in_parquet)
    
    # Filter 10 for test download early
    if args.test_download:
        df = df.head(10).copy()
        
    chunks = get_active_months(df, config['margin_degrees'])
    
    if args.dry_run:
        print("--- DRY RUN REPORT ---")
        print(f"Total observations: {len(df)}")
        print(f"Unique coordinates: {df[['latitude', 'longitude']].drop_duplicates().shape[0]}")
        print(f"Unique dates: {df['timestamp'].dt.date.nunique()}")
        print(f"Temporal range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Spatial range: Lat [{df['latitude'].min():.2f}, {df['latitude'].max():.2f}], Lon [{df['longitude'].min():.2f}, {df['longitude'].max():.2f}]")
        print(f"Number of ERA5 requests: {len(chunks)}")
        print(f"Estimated runtime: {len(chunks) * 5} minutes (Queue dependent)")
        print(f"Temporal matching strategy: Nearest hour, max {config['max_temporal_mismatch_minutes']} min difference")
        print(f"Spatial matching strategy: Active month bounding box + {config['margin_degrees']}deg margin")
        return

    if not args.test_download and not args.download:
        print("Please specify --dry-run, --test-download, or --download.")
        return
        
    # Real extraction
    url, key = load_credentials()
    if url and key:
        c = cdsapi.Client(url=url, key=key)
    else:
        c = cdsapi.Client()
    
    out_dir = Path('data/raw/environment/era5')
    if args.test_download:
        out_dir = Path('data/test/era5')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    
    # Process sequentially for testing (or we can ThreadPool if many)
    for i, chunk in enumerate(chunks):
        print(f"[{i+1}/{len(chunks)}] Processing {chunk['year_month']} (Obs: {len(chunk['observations'])})")
        
        nc_file = out_dir / f"era5_wind_{chunk['year_month']}.nc"
        
        if not nc_file.exists():
            days = [str(d).zfill(2) for d in range(1, 32)]
            times = [f"{str(h).zfill(2)}:00" for h in range(24)]
            
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    c.retrieve(
                        config['dataset'],
                        {
                            'product_type': 'reanalysis',
                            'format': config['format'],
                            'variable': config['variables'],
                            'year': str(chunk['year']),
                            'month': str(chunk['month']).zfill(2),
                            'day': days,
                            'time': times,
                            'area': [
                                round(chunk['N'], 2), round(chunk['W'], 2), 
                                round(chunk['S'], 2), round(chunk['E'], 2)
                            ],
                        },
                        str(nc_file)
                    )
                    break # Success
                except Exception as e:
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt * 60 # 1m, 2m
                        print(f"Failed CDS request for {chunk['year_month']}: {e}. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        print(f"Failed to download CDS request for {chunk['year_month']} after {max_retries} attempts: {e}")
                        # Generate missing records
                        failed = []
                        for _, row in chunk['observations'].iterrows():
                            failed.append({
                                'iceberg_id': row['iceberg_id'],
                                'timestamp': row['timestamp'],
                                'latitude': row['latitude'],
                                'longitude': row['longitude'],
                                'u10': np.nan, 'v10': np.nan,
                                'wind_speed_ms': np.nan, 'wind_direction_deg': np.nan,
                                'era5_timestamp': pd.NaT, 'era5_latitude': np.nan, 'era5_longitude': np.nan,
                                'wind_quality_flag': 'MISSING_WIND'
                            })
                        all_results.append(pd.DataFrame(failed))
            if not nc_file.exists():
                continue # Skip extraction if it completely failed
                
        if nc_file.exists():
            res_df = extract_points(nc_file, chunk['observations'], config)
            all_results.append(res_df)
            
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        if args.test_download:
            out_parquet = Path('data/test/era5/iceberg_era5_wind.parquet')
        else:
            out_parquet = Path('data/processed/iceberg_wind.parquet')
            
        final_df.to_parquet(out_parquet, index=False)
        print(f"\nExtraction complete. Results saved to {out_parquet}")

if __name__ == '__main__':
    main()
