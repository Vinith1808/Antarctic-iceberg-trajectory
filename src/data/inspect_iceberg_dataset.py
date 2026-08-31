import os
import geopandas as gpd
from pathlib import Path
import pandas as pd

def inspect_dataset():
    data_dir = Path('data/raw/iceberg/Iceberg vector outline')
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        return
        
    files = sorted(data_dir.glob('*.gpkg'))
    print(f"Found {len(files)} GPKG files.")
    
    all_counts = {}
    min_lat = 90.0
    max_lat = -90.0
    min_lon = 180.0
    max_lon = -180.0
    
    crs = None
    geom_types = set()
    columns = None
    dtypes = {}
    missing_values = {}
    file_sizes = {}
    
    for f in files:
        file_sizes[f.name] = f.stat().st_size
        print(f"Inspecting {f.name} (Size: {file_sizes[f.name] / 1e6:.2f} MB)...")
        try:
            df = gpd.read_file(f)
            
            # Initial schema
            if crs is None:
                crs = df.crs
                columns = list(df.columns)
                dtypes = {c: str(df[c].dtype) for c in df.columns}
            
            # Record geom types across all files
            geom_types.update(df.geometry.geom_type)
                
            all_counts[f.name] = len(df)
            
            # Bounds
            bounds = df.total_bounds # [minx, miny, maxx, maxy]
            min_lon = min(min_lon, bounds[0])
            min_lat = min(min_lat, bounds[1])
            max_lon = max(max_lon, bounds[2])
            max_lat = max(max_lat, bounds[3])
            
            # Missing values
            for col in df.columns:
                nas = int(df[col].isna().sum())
                if nas > 0:
                    missing_values[col] = missing_values.get(col, 0) + nas
                    
        except Exception as e:
            print(f"Failed to read {f.name}: {e}")
            
    print("\n" + "="*40)
    print("--- SUMMARY ---")
    print(f"CRS: {crs}")
    print(f"Geometry Types: {list(geom_types)}")
    print(f"Columns: {columns}")
    print("Data Types:")
    for c, d in dtypes.items():
        print(f"  {c}: {d}")
    print("File Sizes:")
    for fname, size in file_sizes.items():
        print(f"  {fname}: {size/1e6:.2f} MB")
    print("Records per year:")
    for fname, count in all_counts.items():
        print(f"  {fname}: {count}")
    print(f"Total Records: {sum(all_counts.values())}")
    print(f"Longitude Range: [{min_lon:.4f}, {max_lon:.4f}]")
    print(f"Latitude Range:  [{min_lat:.4f}, {max_lat:.4f}]")
    print(f"Missing Values: {missing_values}")

if __name__ == '__main__':
    inspect_dataset()
