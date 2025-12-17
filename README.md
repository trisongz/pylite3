# pylite3

> **Fast, Zero-Copy Python bindings for [lite3](https://github.com/fastserial/lite3).**

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

`pylite3` provides high-performance access to `lite3` formatted data. It follows the **lazy-parsing** philosophy (similar to `pysimdjson` or `simdjson`), allowing you to access specific fields in large documents instantly without paying the cost of full deserialization.

Data is read directly from the underlying memory buffer—**Zero Copy**.

## 🚀 Key Features

-   **Zero-Copy Loading**: Creates a proxy object in **microseconds**, regardless of document size.
-   **Lazy Access**: Values are only materialized to Python objects when you ask for them.
-   **Memory Safe**: Automatically manages the lifetime of the underlying buffer using Python's reference counting.
-   **Pythonic API**: Works like a `dict` (keys/values/items) or `list` (slicing/indexing), but faster.
-   **Native Hooks**: Supports `object_hook`, `default`, and more for custom serialization/deserialization.
-   **Recursive Writers**: Includes a `dumps()` function to serialize complex nested Python structures into `lite3`.

---

## ⚡ Benchmarks

Comparison vs `pysimdjson` for initial load time. Because `pylite3` is lazy, it returns control to your program immediately.

| Dataset | Size | pysimdjson (Parse) | pylite3 (Lazy) | Speedup |
| :--- | :--- | :--- | :--- | :--- |
| **canada.json** | 2.25 MB | 68,768 µs | 5.7 µs | **12,047x** |
| **citm_catalog.json** | 1.72 MB | 49,471 µs | 3.6 µs | **13,803x** |
| **twitter.json** | 631 KB | 24,189 µs | 2.0 µs | **12,354x** |

_See [Functionality & Performance](docs/design.md) for more details._

---

## 📦 Installation

Requires a C compiler and Python 3.9+.

```bash
# Using uv (Recommended)
uv pip install pysimdjson 

# Build from source
git clone --recurse-submodules https://github.com/fastserial/pylite3.git
cd pylite3
# If you already cloned without submodules:
git submodule update --init --recursive
uv pip install -e .
```

---

## 🛠 Usage

### Reading Data

```python
import pylite3

# Assume 'data' is bytes containing encoded lite3 data
obj = pylite3.loads(data)

# Access fields instantly
print(obj["users"][0]["name"])  # 'John Doe'

# Check types without converting
if obj["metadata"].is_object:
    print("Metadata found")

# Iterate object keys (new!)
for key in obj["users"][0]:
    print(f"User key: {key}")

# Slicing support (new!)
first_two_users = obj["users"][:2]

# Convert to standard dictionary
user_dict = dict(obj["users"][0])  # or .as_dict()
```

### Writing Data

```python
import pylite3

payload = {
    "id": 12345,
    "features": ["lazy", "fast"],
    "meta": {"version": 2.0}
}

# Serialize to bytes
encoded_bytes = pylite3.dumps(payload)
```

---

## 📚 Documentation

-   [📥 Installation Guide](docs/installation.md)
-   [📖 API Reference](docs/api.md)
-   [🏗 Design & Performance](docs/design.md)

---

## 🤝 Contributing

Contributions are welcome! Please check the `Makefile` for useful development commands.

```bash
make install    # Install dependencies
make build      # Compile extension
make benchmark  # Run verification
make test       # Run E2E tests
make coverage   # Generate coverage report
```
