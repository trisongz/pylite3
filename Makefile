.PHONY: all install build benchmark clean help

# Default target
all: install build

# Install dependencies and the package in editable mode
install:
	uv pip install -e .

# Build the Cython extension in-place
build:
	uv run python3 setup.py build_ext --inplace

# Run the benchmark script to verify performance
benchmark: build
	uv run examples/benchmark.py

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -f src/*.c
	rm -f src/*.so
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Show help
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies and package in editable mode"
	@echo "  make build      - Compile Cython extension in-place"
	@echo "  make benchmark  - Run the benchmark script"
	@echo "  make clean      - Remove build artifacts and temporary files"
