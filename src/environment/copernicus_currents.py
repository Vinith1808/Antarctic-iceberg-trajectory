import os
import yaml
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

def dry_run_acquisition():
    # Load env variables (ensures .env is respected if present)
    load_dotenv()
    
    # Load config
    config_path = Path('config/copernicus.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    print("--- Copernicus Marine Data Acquisition (DRY RUN) ---")
    print(f"Product ID: {config['product']['id']}")
    print(f"Requested Variables: {config['product']['variables']}")
    
    # Check credentials
    username = os.getenv('COPERNICUSMARINE_USERNAME')
    password = os.getenv('COPERNICUSMARINE_PASSWORD')
    
    if not username or not password:
        print("WARNING: COPERNICUSMARINE_USERNAME or COPERNICUSMARINE_PASSWORD not set in environment.")
    else:
        print("Credentials found in environment.")
        
    # Load iceberg data
    data_path = Path('data/processed/iceberg_motion.parquet')
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        return
        
    df = pd.read_parquet(data_path)
    
    # Temporal bounds
    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    t_margin = pd.Timedelta(days=config['subset']['temporal_margin_days'])
    
    start_date = min_time - t_margin
    end_date = max_time + t_margin
    
    # Spatial bounds
    min_lat = df['latitude'].min()
    max_lat = df['latitude'].max()
    min_lon = df['longitude'].min()
    max_lon = df['longitude'].max()
    s_margin = config['subset']['spatial_margin_degrees']
    
    req_min_lat = max(-90.0, min_lat - s_margin)
    req_max_lat = min(90.0, max_lat + s_margin)
    req_min_lon = max(-180.0, min_lon - s_margin)
    req_max_lon = min(180.0, max_lon + s_margin)
    
    print("\n--- Calculated Subset Bounds ---")
    print(f"Time Range: {start_date.date()} to {end_date.date()}")
    print(f"Latitude Range: [{req_min_lat:.4f}, {req_max_lat:.4f}]")
    print(f"Longitude Range: [{req_min_lon:.4f}, {req_max_lon:.4f}]")
    
    # Calculate estimates
    # Grid resolution is 0.083 x 0.083 degrees
    lat_cells = (req_max_lat - req_min_lat) / 0.083
    lon_cells = (req_max_lon - req_min_lon) / 0.083
    time_steps = (end_date - start_date).days
    
    total_cells_per_step = int(lat_cells * lon_cells)
    total_data_points = total_cells_per_step * time_steps * len(config['product']['variables'])
    
    print("\n--- Data Volume Estimates ---")
    print(f"Spatial Grid: ~{int(lon_cells)} x ~{int(lat_cells)} cells (Total: {total_cells_per_step:,} per time step)")
    print(f"Time Steps: {time_steps} days")
    print(f"Total Data Points (approx): {total_data_points:,}")
    
    print("\n--- Copernicus Subset Request Kwargs ---")
    request_kwargs = {
        "dataset_id": config['product']['dataset_id'],
        "variables": config['product']['variables'],
        "minimum_longitude": req_min_lon,
        "maximum_longitude": req_max_lon,
        "minimum_latitude": req_min_lat,
        "maximum_latitude": req_max_lat,
        "start_datetime": start_date.strftime('%Y-%m-%d %H:%M:%S'),
        "end_datetime": end_date.strftime('%Y-%m-%d %H:%M:%S'),
        "minimum_depth": config['product']['depth']['min_depth'],
        "maximum_depth": config['product']['depth']['max_depth'],
    }
    for k, v in request_kwargs.items():
        print(f"  {k}: {v}")
        
    # Check if all iceberg observations are covered
    # By definition of how we constructed the bounds with positive margins, they are covered, 
    # but let's do a programmatic check to satisfy the requirement
    covered = (
        (df['timestamp'] >= start_date) & 
        (df['timestamp'] <= end_date) &
        (df['latitude'] >= req_min_lat) &
        (df['latitude'] <= req_max_lat) &
        (df['longitude'] >= req_min_lon) &
        (df['longitude'] <= req_max_lon)
    ).all()
    
    print(f"\nAll iceberg observations covered by bounds: {covered}")
    print("\nDRY RUN COMPLETE. No data was downloaded.")

if __name__ == '__main__':
    dry_run_acquisition()
