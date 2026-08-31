import os
import copernicusmarine
from dotenv import load_dotenv

def test_access():
    load_dotenv()
    
    username = os.getenv('COPERNICUSMARINE_USERNAME')
    password = os.getenv('COPERNICUSMARINE_PASSWORD')
    
    if not username or not password:
        print("Credentials not found in environment (COPERNICUSMARINE_USERNAME / COPERNICUSMARINE_PASSWORD).")
        print("Skipping active authentication test.")
        # We can still test anonymous metadata fetch if dataset allows, or just print a warning.
        
    print("Testing metadata query for cmems_mod_glo_phy_my_0.083deg_P1D-m...")
    try:
        # We use describe() to check if the client can reach the catalog and query the dataset
        catalog = copernicusmarine.describe(
            dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m"
        )
        print("Metadata fetch successful. Connection is working.")
        
    except Exception as e:
        print(f"Error accessing Copernicus Marine Service: {e}")

if __name__ == '__main__':
    test_access()
