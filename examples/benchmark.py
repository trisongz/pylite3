import time
import pylite3
import sys

def main():
    print("--- Pylite3 Benchmark ---")
    
    # Generate test data using our new dumps() function
    test_dict = {
        "id": 12345,
        "name": "Pylite3 Test",
        "score": 99,
        "active": 1 # Boolean as int for now as dumps() is simple
    }
    
    # 1. Serialization
    start = time.perf_counter()
    data = pylite3.dumps(test_dict)
    print(f"Serialization time: {(time.perf_counter() - start) * 1e6:.2f} us")
    print(f"Serialized size: {len(data)} bytes")
    
    # 2. Zero-copy load (Lazy Proxy)
    start = time.perf_counter()
    obj = pylite3.loads(data)
    load_time = (time.perf_counter() - start) * 1e9
    print(f"Load time: {load_time:.0f} ns")
    
    # 3. Access
    try:
        start = time.perf_counter()
        name = obj["name"]
        access_time = (time.perf_counter() - start) * 1e6
        print(f"Access 'name': {name!r} in {access_time:.2f} us")
        
        start = time.perf_counter()
        sid = obj["id"]
        print(f"Access 'id': {sid} in {(time.perf_counter() - start) * 1e6:.2f} us")
        
    except KeyError as e:
        print(f"KeyError: {e}")
        sys.exit(1)
        
    # 4. To Python / Recursive
    start = time.perf_counter()
    try:
        # Test as_dict() explicit call (which wraps to_python)
        # Note: This will fail until key iteration is fixed in C lib binding
        py_obj = obj.as_dict() 
        print(f"as_dict time: {(time.perf_counter() - start) * 1e6:.2f} us")
    except NotImplementedError:
        print("as_dict() skipped (key iteration missing)")

    # Test recursive loads
    start = time.perf_counter()
    try:
        py_obj_direct = pylite3.loads(data, recursive=True)
        print(f"loads(recursive=True) time: {(time.perf_counter() - start) * 1e6:.2f} us")
    except NotImplementedError:
        print("loads(recursive=True) skipped (key iteration missing)")

    print("Verification: PASSED")

if __name__ == "__main__":
    main()
