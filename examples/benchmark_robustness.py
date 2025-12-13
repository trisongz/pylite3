
import time
import pylite3
import json
from datetime import datetime

def benchmark_hooks():
    print("\n--- Benchmark: Hooks & Recursion ---")
    
    # 1. Test Dumps with Default Hook
    print("1. Dumps with Default Hook (datetime)")
    data_with_date = {
        "id": 1,
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "nested": {"updated_at": datetime(2023, 1, 2, 12, 0, 0)}
    }
    
    def date_handler(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
        
    start = time.perf_counter()
    encoded = pylite3.dumps(data_with_date, default=date_handler)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   pylite3.dumps(default=...): {duration:.2f} us")
    print(f"   Size: {len(encoded)} bytes")
    
    # Compare with json
    start = time.perf_counter()
    json_encoded = json.dumps(data_with_date, default=date_handler)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   json.dumps(default=...):    {duration:.2f} us")
    
    # 2. Test Loads with Object Hook
    print("\n2. Loads with Object Hook")
    
    def date_hook(dct):
        if 'created_at' in dct:
            # lightweight hook simulation
            pass
        return dct
        
    start = time.perf_counter()
    _ = pylite3.loads(encoded, recursive=True, object_hook=date_hook)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   pylite3.loads(recursive=True, hook): {duration:.2f} us")
    
    start = time.perf_counter()
    _ = json.loads(json_encoded, object_hook=date_hook)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   json.loads(hook):                    {duration:.2f} us")


def benchmark_slicing():
    print("\n--- Benchmark: Array Slicing ---")
    
    # Create large array
    large_list = list(range(10000))
    encoded = pylite3.dumps(large_list)
    obj = pylite3.loads(encoded)
    
    print(f"Array size: {len(large_list)}")
    
    # Slice first 100
    start = time.perf_counter()
    slice1 = obj[:100]
    duration = (time.perf_counter() - start) * 1e6
    print(f"   pylite3 slice [:100]: {duration:.2f} us")
    
    start = time.perf_counter()
    json_slice = large_list[:100]
    duration = (time.perf_counter() - start) * 1e6
    print(f"   list slice [:100]:    {duration:.2f} us")
    
    # Slice step
    start = time.perf_counter()
    slice2 = obj[::100] # Stride
    duration = (time.perf_counter() - start) * 1e6
    print(f"   pylite3 slice [::100]: {duration:.2f} us")

def benchmark_mapping():
    print("\n--- Benchmark: Mapping / Dict Conversion ---")
    
    data = {"k" + str(i): i for i in range(1000)}
    encoded = pylite3.dumps(data)
    obj = pylite3.loads(encoded)
    
    start = time.perf_counter()
    d = dict(obj)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   dict(obj) [size=1000]: {duration:.2f} us")
    
    start = time.perf_counter()
    # Baseline: dict copy
    d2 = dict(data)
    duration = (time.perf_counter() - start) * 1e6
    print(f"   dict(dict) [baseline]: {duration:.2f} us")

def main():
    benchmark_hooks()
    benchmark_slicing()
    benchmark_mapping()

if __name__ == "__main__":
    main()
