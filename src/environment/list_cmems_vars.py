import json
import re

def list_vars():
    with open('cmems_meta.json', 'r', encoding='utf-16') as f:
        raw = f.read()
    
    idx = raw.find('{')
    if idx == -1:
        print("No JSON found")
        return
        
    data = json.loads(raw[idx:])
    
    siconc_data = None
    def find_siconc(obj):
        nonlocal siconc_data
        if isinstance(obj, dict):
            if obj.get('short_name') == 'siconc':
                siconc_data = obj
            for v in obj.values():
                find_siconc(v)
        elif isinstance(obj, list):
            for i in obj:
                find_siconc(i)

    find_siconc(data)
    print(json.dumps(siconc_data, indent=2))

if __name__ == '__main__':
    list_vars()
