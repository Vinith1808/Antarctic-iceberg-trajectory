import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd

def create_visualizations():
    in_path = Path('data/processed/iceberg_motion.parquet')
    if not in_path.exists():
        print("Data not found. Run calculate_motion.py first.")
        return
        
    out_dir = Path('docs/figures')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_parquet(in_path)
    
    # 1. Trajectories on Antarctic Map
    plt.figure(figsize=(10, 10))
    # Pick top 10 icebergs by observation count
    top_icebergs = df['iceberg_id'].value_counts().head(10).index
    
    for ibg in top_icebergs:
        track = df[df['iceberg_id'] == ibg]
        plt.plot(track['x_m'], track['y_m'], marker='.', markersize=4, label=ibg, linewidth=1.5)
        
    plt.title('Top 10 Iceberg Trajectories (EPSG:3031)')
    plt.xlabel('Easting (m)')
    plt.ylabel('Northing (m)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axis('equal')
    plt.savefig(out_dir / 'trajectories_map.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Velocity distribution
    plt.figure(figsize=(8, 5))
    valid_vel = df['velocity_ms'].dropna()
    valid_vel = valid_vel[valid_vel < 3.0] # Ignore highly anomalous for plotting
    
    plt.hist(valid_vel, bins=50, edgecolor='black', alpha=0.7)
    plt.title('Iceberg Velocity Distribution (< 3 m/s)')
    plt.xlabel('Velocity (m/s)')
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.savefig(out_dir / 'velocity_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Time gap distribution
    plt.figure(figsize=(8, 5))
    gaps = df['time_since_previous_observation_hours'].dropna()
    gaps_days = gaps / 24.0
    gaps_days = gaps_days[gaps_days < 60] # zoom in on gaps < 2 months
    
    plt.hist(gaps_days, bins=30, edgecolor='black', alpha=0.7)
    plt.title('Time Gap Distribution (< 60 Days)')
    plt.xlabel('Gap (Days)')
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.savefig(out_dir / 'time_gap_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {out_dir}")

if __name__ == '__main__':
    create_visualizations()
