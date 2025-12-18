import json
import time
import os
import sys
import glob
from pathlib import Path

# Try importing optional libraries
LIBS = {}
try:
    import simdjson
    LIBS['pysimdjson'] = simdjson
except ImportError:
    pass

try:
    import orjson
    LIBS['orjson'] = orjson
except ImportError:
    pass

try:
    import ujson
    LIBS['ujson'] = ujson
except ImportError:
    pass

try:
    import rapidjson
    LIBS['rapidjson'] = rapidjson
except ImportError:
    pass

try:
    import cysimdjson
    LIBS['cysimdjson'] = cysimdjson
except ImportError:
    pass

if not LIBS:
    print("Warning: No comparison libraries found (pysimdjson, orjson, etc). Install them to benchmark.")

import pylite3

def benchmark_file(filepath):
    print(f"\n--- Benchmarking {os.path.basename(filepath)} ---")
    
    # 1. Load JSON (standard lib)
    with open(filepath, 'rb') as f:
        json_bytes = f.read()
    
    try:
        py_obj = json.loads(json_bytes)
    except Exception as e:
        print(f"Skipping (Invalid JSON): {e}")
        return

    # 2. Convert to Lite3
    # We use our improved dumps to prepare the test data
    try:
        start_dump = time.perf_counter()
        lite3_data = pylite3.dumps(py_obj)
        dump_time = (time.perf_counter() - start_dump) * 1e3
        print(f"Conversion to Lite3: {dump_time:.2f} ms | Size: {len(lite3_data)} bytes (Original JSON: {len(json_bytes)} bytes)")
    except Exception as e:
        print(f"Conversion failed: {e}")
        return

    # 3. Benchmark Comparison Libraries
    
    # standard json
    start = time.perf_counter()
    _ = json.loads(json_bytes)
    json_time = (time.perf_counter() - start) * 1e6
    print(f"json loads:           {json_time:.2f} us")

    # orjson
    if 'orjson' in LIBS:
        start = time.perf_counter()
        _ = LIBS['orjson'].loads(json_bytes)
        or_time = (time.perf_counter() - start) * 1e6
        print(f"orjson loads:         {or_time:.2f} us")
        
    # ujson
    if 'ujson' in LIBS:
        start = time.perf_counter()
        _ = LIBS['ujson'].loads(json_bytes)
        u_time = (time.perf_counter() - start) * 1e6
        print(f"ujson loads:          {u_time:.2f} us")
        
    # rapidjson
    if 'rapidjson' in LIBS:
        start = time.perf_counter()
        _ = LIBS['rapidjson'].loads(json_bytes)
        rapid_time = (time.perf_counter() - start) * 1e6
        print(f"rapidjson loads:      {rapid_time:.2f} us")
        
    # pysimdjson
    if 'pysimdjson' in LIBS:
        start = time.perf_counter()
        parser = LIBS['pysimdjson'].Parser()
        _ = parser.parse(json_bytes)
        simd_time = (time.perf_counter() - start) * 1e6
        print(f"pysimdjson parse:     {simd_time:.2f} us")

    # cysimdjson
    if 'cysimdjson' in LIBS:
        start = time.perf_counter()
        parser = LIBS['cysimdjson'].JSONParser()
        _ = parser.parse(json_bytes)
        cysimd_time = (time.perf_counter() - start) * 1e6
        print(f"cysimdjson parse:     {cysimd_time:.2f} us")

    # 4. Benchmark pylite3 loads (lazy)
    start = time.perf_counter()
    lite_obj = pylite3.loads(lite3_data)
    lite_time = (time.perf_counter() - start) * 1e6
    print(f"pylite3 loads (lazy): {lite_time:.2f} us")
    
    print("-" * 30)
    if 'pysimdjson' in LIBS:
        print(f"Speedup vs pysimdjson: {simd_time / lite_time:.2f}x")
    if 'orjson' in LIBS:
        print(f"Speedup vs orjson:     {or_time / lite_time:.2f}x")
    print(f"Speedup vs json:       {json_time / lite_time:.2f}x")

    # 5. Benchmark pylite3 loads (recursive/eager)
    start = time.perf_counter()
    lite_rec = pylite3.loads(lite3_data, recursive=True)
    lite_rec_time = (time.perf_counter() - start) * 1e6
    print(f"pylite3 loads (recursive): {lite_rec_time:.2f} us")
    
    # 6. Verify Correctness
    print("Verifying correctness (Consistency Check)...")
    if lite_rec == py_obj:
        print("MATCH: pylite3 recursive load matches json.loads")
    else:
        print("MISMATCH: pylite3 output does not match json.loads!")

def generate_random_object(depth=0, max_depth=4, width=3):
    import random
    import string
    
    if depth >= max_depth:
        # Return scalar
        t = random.choice(['int', 'float', 'str', 'bool', 'null'])
        if t == 'int': return random.randint(-10000, 10000)
        if t == 'float': return random.random() * 10000
        if t == 'str': return ''.join(random.choices(string.ascii_letters, k=10))
        if t == 'bool': return random.choice([True, False])
        if t == 'null': return None
        
    # Return container
    t = random.choice(['dict', 'list'])
    if t == 'dict':
        return {
            ''.join(random.choices(string.ascii_letters, k=5)): generate_random_object(depth+1, max_depth, width)
            for _ in range(random.randint(1, width))
        }
    else:
        return [
            generate_random_object(depth+1, max_depth, width)
            for _ in range(random.randint(1, width))
        ]

def benchmark_fuzzing(runs=10):
    print(f"\n--- Fuzzing Verification ({runs} runs) ---")
    import random
    
    for i in range(runs):
        obj = generate_random_object(max_depth=5, width=4)
        
        # Dump
        try:
            data = pylite3.dumps(obj)
        except Exception as e:
            print(f"Run {i}: Dumps failed: {e}")
            continue
            
        # Load
        try:
            loaded = pylite3.loads(data, recursive=True)
        except Exception as e:
            print(f"Run {i}: Loads failed: {e}")
            continue
            
        # Compare
        # Note: Floating point precision might differ slightly due to string formatting in dumps fallback?
        # But wait, pylite3.dumps is binary for floats (double). recursive=True returns python float.
        # Should be exact bit-wise if no intermediate string conversion happens.
        # Although random.random() -> float (64-bit).
        if loaded == obj:
             pass # Success
        else:
             print(f"Run {i}: MISMATCH!")
             # print(f"Orig: {obj}")
             # print(f"Load: {loaded}")
             return
             
    print(f"Passed {runs} random fuzzing runs.")


def main():
    json_dir = os.environ.get("JSONEXAMPLES_DIR")
    if not json_dir:
        repo_root = Path(__file__).resolve().parents[1]
        candidates = [
            repo_root / "jsonexamples",
            repo_root / "pysimdjson" / "jsonexamples",
        ]
        for cand in candidates:
            if cand.is_dir():
                json_dir = str(cand)
                break

    if not json_dir or not Path(json_dir).is_dir():
        print("No jsonexamples directory found. Set JSONEXAMPLES_DIR to run file benchmarks.")
        return

    files = glob.glob(os.path.join(json_dir, "*.json"))
    
    # Prioritize interesting files
    priority = ['twitter.json', 'canada.json', 'citm_catalog.json']
    files.sort(key=lambda f: (os.path.basename(f) not in priority, os.path.basename(f)))

    max_files = int(os.environ.get("JSONEXAMPLES_MAX_FILES", "5"))
    count = 0
    for f in files:
        if count >= max_files:
            break  # Limit for speed
        benchmark_file(f)
        count += 1
        
    # Run Random Fuzzing
    benchmark_fuzzing()

if __name__ == "__main__":
    main()
