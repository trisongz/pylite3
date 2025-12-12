# Installation

`pylite3` is a Cython extension that requires compilation.

## Prerequisites

- Python 3.9+
- C Compiler (Clang on macOS, GCC on Linux, MSVC on Windows)
- `uv` (recommended) or `pip`

## Installing from Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fastserial/pylite3.git
   cd pylite3
   # Initialize submodule
   git submodule update --init --recursive
   ```

2. **Install with `uv` (Recommended)**:
   ```bash
   # Create virtual environment and install in editable mode
   uv pip install -e .
   ```

3. **Install with `pip`**:
   ```bash
   pip install .
   ```

## Development Setup

For contributors who want to run benchmarks or modify the Cython bindings:

```bash
# Install dependencies
uv sync

# Build in-place
make build

# Run benchmarks
make benchmark

# Run tests
make test

# Generate coverage report
make coverage
```
