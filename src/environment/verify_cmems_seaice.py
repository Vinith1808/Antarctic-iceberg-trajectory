import copernicusmarine

def verify():
    # Load the catalogue
    catalogue = copernicusmarine.read_catalogue()
    
    product_id = 'GLOBAL_MULTIYEAR_PHY_001_030'
    print(f"Searching for product: {product_id}")
    
    # We used 'cmems_mod_glo_phy_my_0.083deg_P1D-m' for daily data in phase 5
    dataset_id = 'cmems_mod_glo_phy_my_0.083deg_P1D-m'
    
    try:
        product = catalogue.get_product(product_id)
        print(f"\nProduct found: {product.title}")
        print(f"Product ID: {product.product_id}")
        
        for dataset in product.datasets:
            print(f"\nDataset: {dataset.dataset_id}")
            print(f"Temporal range: {dataset.temporal_extent.start} to {dataset.temporal_extent.end}")
            
            # Check variables
            if dataset.variables:
                for var in dataset.variables:
                    if 'ice' in var.standard_name.lower() or 'sic' in var.short_name.lower() or 'siconc' in var.short_name.lower():
                        print(f"  -> Found Sea Ice Var: {var.short_name}")
                        print(f"     Standard Name: {var.standard_name}")
                        print(f"     Long Name: {var.long_name}")
                        print(f"     Units: {var.units}")
    except Exception as e:
        print(f"Error accessing catalogue: {e}")

if __name__ == '__main__':
    verify()
