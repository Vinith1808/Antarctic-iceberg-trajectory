import pandas as pd

def analyze_coverage():
    df = pd.read_parquet('data/processed/iceberg_motion.parquet')
    
    print(f"Total observations: {len(df)}")
    print(f"Unique iceberg IDs: {df['iceberg_id'].nunique()}")
    print(f"Unique dates: {df['timestamp'].dt.date.nunique()}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Latitude range: {df['latitude'].min()} to {df['latitude'].max()}")
    print(f"Longitude range: {df['longitude'].min()} to {df['longitude'].max()}")
    
    unique_coords = df[['latitude', 'longitude']].drop_duplicates()
    print(f"Unique coordinates: {len(unique_coords)}")
    
    df['year_month'] = df['timestamp'].dt.to_period('M')
    print(f"Unique year-months: {df['year_month'].nunique()}")

if __name__ == '__main__':
    analyze_coverage()
