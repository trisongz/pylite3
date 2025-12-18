# Design and Performance

## Zero-Copy Architecture

`pylite3` is designed for extreme performance by avoiding memory copying whenever possible. When you call `loads(bytes)`, it **does not** parse the entire buffer. Instead, it creates a lightweight `Lite3Object` proxy that points to the data within the original byte buffer.

### How it works

1.  **Lazy Evaluation**: Values are only decoded when you access them (e.g., `obj["user"]["id"]`).
2.  **Memory Safety**: The `Lite3Object` holds a reference to a stable exported buffer (internally a `memoryview`), which keeps the underlying memory alive and prevents unsafe mutation while any proxy exists.
3.  **No Intermediate Structures**: Standard JSON parsers typically build a massive tree of Python `dict` and `list` objects. `pylite3` reads directly from the binary buffer, bypassing this expensive allocation phase.

## Correctness and portability notes

- Scalar decoding uses lite3’s accessor functions (which use `memcpy`) to avoid unaligned/UB reads on strict-alignment platforms.
- `loads()` performs early sanity checks on the root value so malformed inputs fail cleanly instead of crashing.

## Benchmarks

Because of its lazy nature, `pylite3`'s distinct advantage is in "Time to First Byte" or random access patterns.

| Dataset | Size | pysimdjson (Parsing) | pylite3 (Lazy Load) | Speedup |
| :--- | :--- | :--- | :--- | :--- |
| **canada.json** | 2.25 MB | ~68 ms | ~5.7 µs | **12,047x** |
| **twitter.json** | 631 KB | ~24 ms | ~2.0 µs | **12,354x** |

### When to use `pylite3`?

- **High Throughput**: You have massive streams of data but only need to inspect a few fields.
- **Memory Constrained**: You can't afford to de-serialize large blobs into 5x-10x larger Python dictionary structures.
- **Random Access**: You need to grab a value at `obj["data"][0]["id"]` without parsing the gigabytes of irrelevant data surrounding it.

## Writing performance

`dumps()` uses the lite3 writer API and grows its internal buffer as needed. For small objects, this avoids allocating large fixed buffers per call.
