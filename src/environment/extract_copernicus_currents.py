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
VARIABLES = ["uo", "vo"]
DEPTH_MIN = 0.493
DEPTH_MAX = 0.4942
SPATIAL_MARGIN = 0.5  # degrees
GAP_THRESHOLD_HOURS = 720  # 30 days gap is too large to interpolate

def get_chunks(df):
    """Group observations by iceberg and month to create manageable download chunks."""
    # Filter out anomalous jumps to avoid massive bounding boxes
    valid = df[df['motion_quality_flag'] != 'ANOMALOUS_VELOCITY'].copy()
    valid['year_month'] = valid['timestamp'].dt.to_period('M')
    
    chunks = []
    for (iceberg_id, ym), group in valid.groupby(['iceberg_id', 'year_month']):
        chunk = {
            'iceberg_id': iceberg_id,
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
        
        # Handle wrap around
        if chunk['min_lon'] < -180: chunk['min_lon'] = -180.0
        if chunk['max_lon'] > 180: chunk['max_lon'] = 180.0
            
        chunks.append(chunk)
    return chunks

def download_chunk(chunk, out_dir, use_mock=False):
    """Download a specific chunk using Copernicus Marine toolbox, or mock if requested."""
    out_file = out_dir / f"{chunk['iceberg_id']}_{chunk['year_month']}.nc"
    if out_file.exists():
        return out_file
        
    print(f"Downloading {out_file.name}...")
    
    if use_mock:
        print("MOCK MODE: Creating mock test data for validation...")
        times = pd.date_range(chunk['min_time'], chunk['max_time'], freq='D')
        lats = np.arange(chunk['min_lat'], chunk['max_lat'] + 0.083, 0.083)
        lons = np.arange(chunk['min_lon'], chunk['max_lon'] + 0.083, 0.083)
        uo_data = np.full((len(times), 1, len(lats), len(lons)), 0.1, dtype=np.float32)
        vo_data = np.full((len(times), 1, len(lats), len(lons)), 0.05, dtype=np.float32)
        
        ds = xr.Dataset(
            {
                "uo": (["time", "depth", "latitude", "longitude"], uo_data),
                "vo": (["time", "depth", "latitude", "longitude"], vo_data)
            },
            coords={"time": times, "depth": [DEPTH_MIN], "latitude": lats, "longitude": lons}
        )
        ds.to_netcdf(out_file)
        return out_file
        
    # Real download
    username = os.getenv('COPERNICUSMARINE_USERNAME')
    password = os.getenv('COPERNICUSMARINE_PASSWORD')
    if not username or not password:
        print("ERROR: Credentials not set in environment variables (COPERNICUSMARINE_USERNAME, COPERNICUSMARINE_PASSWORD).")
        print("Please configure your .env file.")
        raise ValueError("Missing Copernicus Marine credentials for real download.")
        
    copernicusmarine.subset(
        dataset_id=DATASET_ID,
        variables=VARIABLES,
        minimum_longitude=chunk['min_lon'],
        maximum_longitude=chunk['max_lon'],
        minimum_latitude=chunk['min_lat'],
        maximum_latitude=chunk['max_lat'],
        start_datetime=chunk['min_time'].strftime('%Y-%m-%d %H:%M:%S'),
        end_datetime=chunk['max_time'].strftime('%Y-%m-%d %H:%M:%S'),
        minimum_depth=DEPTH_MIN,
        maximum_depth=DEPTH_MAX,
        output_filename=out_file.name,
        output_directory=str(out_dir),
        force_download=True,
        username=username,
        password=password
    )
    return out_file

def extract_points(chunk_file, observations):
    """Extract nearest neighbor points from the downloaded NetCDF for given observations."""
    try:
        ds = xr.open_dataset(chunk_file)
    except Exception as e:
        print(f"Failed to open NetCDF {chunk_file}: {e}")
        return pd.DataFrame()
        
    results = []
    
    for _, row in observations.iterrows():
        result = {
            'iceberg_id': row['iceberg_id'],
            'timestamp': row['timestamp'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'uo': np.nan,
            'vo': np.nan,
            'current_speed_ms': np.nan,
            'current_direction_deg': np.nan,
            'copernicus_timestamp': pd.NaT,
            'copernicus_latitude': np.nan,
            'copernicus_longitude': np.nan,
            'surface_depth_m': DEPTH_MIN,
            'current_quality_flag': 'VALID'
        }
        
        try:
            # Nearest neighbor extraction
            point_data = ds.sel(
                longitude=row['longitude'],
                latitude=row['latitude'],
                time=row['timestamp'],
                method='nearest'
            )
            
            # Surface depth
            if 'depth' in point_data.coords:
                point_data = point_data.isel(depth=0)
                
            uo = float(point_data['uo'].values)
            vo = float(point_data['vo'].values)
            
            c_time = pd.to_datetime(point_data['time'].values)
            c_lat = float(point_data['latitude'].values)
            c_lon = float(point_data['longitude'].values)
            
            result['uo'] = uo
            result['vo'] = vo
            result['copernicus_timestamp'] = c_time
            result['copernicus_latitude'] = c_lat
            result['copernicus_longitude'] = c_lon
            
            if np.isnan(uo) or np.isnan(vo):
                result['current_quality_flag'] = 'MISSING_CURRENT'
            else:
                result['current_speed_ms'] = np.sqrt(uo**2 + vo**2)
                # 0=North, 90=East
                result['current_direction_deg'] = np.degrees(np.arctan2(uo, vo)) % 360
                
                # Check spatial/temporal mismatch
                # time diff in hours
                time_diff_hours = abs((row['timestamp'] - c_time).total_seconds()) / 3600.0
                if time_diff_hours > 24:
                    result['current_quality_flag'] = 'TEMPORAL_MISMATCH'
                elif abs(row['latitude'] - c_lat) > 0.1 or abs(row['longitude'] - c_lon) > 0.1:
                    result['current_quality_flag'] = 'SPATIAL_MISMATCH'
                    
        except KeyError as e:
            result['current_quality_flag'] = 'OUTSIDE_COVERAGE'
        except Exception as e:
            result['current_quality_flag'] = 'MISSING_CURRENT'
            
        results.append(result)
            
    ds.close()
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Extract Copernicus Currents")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without downloading')
    parser.add_argument('--download', action='store_true', help='Perform the actual download (production)')
    parser.add_argument('--test-real-download', action='store_true', help='Perform a real test download')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real API')
    parser.add_argument('--max-observations', type=int, help='Limit number of observations to process')
    parser.add_argument('--start-date', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='End date YYYY-MM-DD')
    
    args = parser.parse_args()
    
    if args.mock and (args.download or args.test_real_download):
        print("ERROR: --mock cannot be used with --download or --test-real-download. Aborting.")
        return
        
    df = pd.read_parquet('data/processed/iceberg_motion.parquet')
    
    # Apply filters
    if args.start_date:
        df = df[df['timestamp'] >= pd.to_datetime(args.start_date)]
    if args.end_date:
        df = df[df['timestamp'] <= pd.to_datetime(args.end_date)]
    if args.max_observations:
        df = df.head(args.max_observations)
        
    chunks = get_chunks(df)
    
    total_obs = sum(c['obs_count'] for c in chunks)
    unique_coords = df[['latitude', 'longitude']].drop_duplicates().shape[0]
    unique_dates = df['timestamp'].dt.date.nunique()
    min_t = df['timestamp'].min()
    max_t = df['timestamp'].max()
    min_lat, max_lat = df['latitude'].min(), df['latitude'].max()
    min_lon, max_lon = df['longitude'].min(), df['longitude'].max()
    
    # Estimations
    est_grid_points = sum(
        ((c['max_lat'] - c['min_lat']) / 0.083) * 
        ((c['max_lon'] - c['min_lon']) / 0.083) * 
        max(1, (c['max_time'] - c['min_time']).days)
        for c in chunks
    )
    est_size_mb = (est_grid_points * 2 * 4) / (1024 * 1024) # 2 vars, 4 bytes float32
    
    print("--- DRY RUN REPORT ---")
    print(f"Observations: {total_obs}")
    print(f"Unique icebergs: {df['iceberg_id'].nunique()}")
    print(f"Unique dates: {unique_dates}")
    print(f"Temporal range: {min_t} to {max_t}")
    print(f"Spatial range: Lat [{min_lat:.2f}, {max_lat:.2f}], Lon [{min_lon:.2f}, {max_lon:.2f}]")
    print(f"Requested tiles/chunks: {len(chunks)}")
    print(f"Estimated downloaded size: {est_size_mb:.2f} MB")
    print(f"Estimated grid points: {int(est_grid_points):,}")
    print(f"Estimated API requests: {len(chunks)}")
    print(f"Estimated execution time: {len(chunks) * 10 / 60:.2f} minutes")
    print("----------------------")
    
    if args.dry_run:
        return
        
    if args.download or args.test_real_download or args.mock:
        if args.download:
            out_dir = Path('data/raw/environment/copernicus')
            out_parquet = Path('data/processed/iceberg_currents.parquet')
        elif args.test_real_download:
            out_dir = Path('data/test/copernicus_real')
            out_parquet = Path('data/test/copernicus_real/iceberg_currents.parquet')
        else:
            out_dir = Path('data/test/copernicus')
            out_parquet = Path('data/test/copernicus/iceberg_currents.parquet')
            
        out_dir.mkdir(parents=True, exist_ok=True)
        out_parquet.parent.mkdir(parents=True, exist_ok=True)
        
        import concurrent.futures
        
        all_results = []
        
        print(f"Starting concurrent downloads with 10 workers for {len(chunks)} chunks...")
        # Download concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_chunk = {
                executor.submit(download_chunk, chunk, out_dir, args.mock): chunk 
                for chunk in chunks
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
                chunk = future_to_chunk[future]
                try:
                    nc_file = future.result()
                    print(f"[{i+1}/{len(chunks)}] Downloaded {nc_file.name} for {chunk['iceberg_id']} {chunk['year_month']}")
                    # Extract points
                    res_df = extract_points(nc_file, chunk['observations'])
                    all_results.append(res_df)
                except Exception as e:
                    print(f"[{i+1}/{len(chunks)}] Failed chunk {chunk['iceberg_id']} {chunk['year_month']}: {e}")
                    # Create empty DataFrame for failed chunks to preserve rows
                    failed_results = []
                    for _, row in chunk['observations'].iterrows():
                        failed_results.append({
                            'iceberg_id': row['iceberg_id'],
                            'timestamp': row['timestamp'],
                            'latitude': row['latitude'],
                            'longitude': row['longitude'],
                            'uo': np.nan,
                            'vo': np.nan,
                            'current_speed_ms': np.nan,
                            'current_direction_deg': np.nan,
                            'copernicus_timestamp': pd.NaT,
                            'copernicus_latitude': np.nan,
                            'copernicus_longitude': np.nan,
                            'surface_depth_m': DEPTH_MIN,
                            'current_quality_flag': 'OUTSIDE_COVERAGE' if 'exceed the dataset coordinates' in str(e) else 'MISSING_CURRENT'
                        })
                    all_results.append(pd.DataFrame(failed_results))
                
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            # Ensure row counts match (we processed every row in chunks)
            final_df.to_parquet(out_parquet, index=False)
            print(f"\nExtraction complete. Results saved to {out_parquet}")
            
if __name__ == '__main__':
    main()
