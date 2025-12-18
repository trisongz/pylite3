# Contributing

## Development setup

```bash
uv sync --group dev
uv pip install -e .
```

## Useful commands

```bash
uv run pytest
uv build --sdist
make build
make benchmark
```

## Submodules

The lite3 C library is included as a git submodule under `vendor/lite3`.

When cloning for development:

```bash
git clone --recurse-submodules https://github.com/fastserial/pylite3.git
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

