import json
import subprocess
from datetime import datetime

def check_metadata():
    print("Fetching metadata for cmems_mod_glo_phy_my_0.083deg_P1D-m...")
    result = subprocess.run(
        ['.venv/Scripts/copernicusmarine.exe', 'describe', '--dataset-id', 'cmems_mod_glo_phy_my_0.083deg_P1D-m'],
        capture_output=True, text=True
    )
    
    # It outputs JSON text
    try:
        data = json.loads(result.stdout)
    except Exception as e:
        print("Could not parse JSON:", e)
        # Try to find the start of json if there is any warning
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('{'):
                data = json.loads('\n'.join(lines[i:]))
                break
        else:
            return

    # find siconc
    all_vars = []
    siconc_var = None
    if 'products' in data:
        prod = data['products'][0]
        ds = prod['datasets'][0]
        for service in ds.get('services', []):
            if 'variables' in service:
                for var in service['variables']:
                    all_vars.append(f"{var.get('short_name')} ({var.get('standard_name')})")
                    if var.get('short_name') in ['siconc', 'sial', 'sivol', 'sithick', 'icec'] or 'ice' in (var.get('standard_name') or '').lower():
                        siconc_var = var

    if not siconc_var:
        print("siconc NOT FOUND")
        print("Available vars:", all_vars)
        return

    print("1. Dataset ID: cmems_mod_glo_phy_my_0.083deg_P1D-m")
    print("2. Product ID: GLOBAL_MULTIYEAR_PHY_001_030")
    print(f"3. Variable name: {siconc_var.get('short_name')}")
    print(f"4. Description: {siconc_var.get('standard_name')} / {siconc_var.get('long_name')}")
    print(f"5. Units: {siconc_var.get('units')}")
    
    time_coord = next((c for c in siconc_var.get('coordinates', []) if c['coordinate_id'] == 'time'), None)
    lat_coord = next((c for c in siconc_var.get('coordinates', []) if c['coordinate_id'] == 'latitude'), None)
    lon_coord = next((c for c in siconc_var.get('coordinates', []) if c['coordinate_id'] == 'longitude'), None)
    depth_coord = next((c for c in siconc_var.get('coordinates', []) if c['coordinate_id'] == 'depth'), None)
    
    print(f"8. Spatial resolution: {lat_coord['step']} degrees")
    if time_coord:
        tmin = datetime.utcfromtimestamp(time_coord['minimum_value']/1000).strftime('%Y-%m-%d')
        tmax = datetime.utcfromtimestamp(time_coord['maximum_value']/1000).strftime('%Y-%m-%d')
        print(f"9. Temporal resolution: {time_coord['step']/1000/3600/24} days")
        print(f"10. Available date range: {tmin} to {tmax}")
    
    if lat_coord:
        print(f"11. Spatial coverage: Lat {lat_coord['minimum_value']} to {lat_coord['maximum_value']}, Lon {lon_coord['minimum_value']} to {lon_coord['maximum_value']}")
        
    print(f"12. Depth level: {'Required' if depth_coord else 'Surface only (no depth coordinate)'}")

if __name__ == '__main__':
    check_metadata()
