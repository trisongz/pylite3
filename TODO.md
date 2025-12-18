# TODO: `pylite3` design improvements

This file tracks prioritized follow-ups for `pylite3`. We’ll implement these sequentially and validate each step before moving on.

## Baseline checks (run before/after each change)

- [x] `uv sync --group dev`
- [x] `uv run pytest`
- [x] `uv build --sdist`

## Phase 1 — Safety + correctness (highest priority)

### 1) Avoid unaligned/UB scalar reads

- [x] Replace direct pointer-casts for `i64`/`f64` reads with lite3 accessors (`lite3_val_i64`, `lite3_val_f64`).
  - Target: `src/pylite3.pyx` (scalar materialization path).
- [x] Replace manual string/bytes slicing logic with lite3 accessors (`lite3_val_str_n`, `lite3_val_bytes`) for correct length handling.
  - Target: `src/pylite3.pyx`.
- [x] Add tests that exercise scalar decoding on multiple platforms (at least via CI) and include a “stress” case with many numeric fields.
  - Target: `tests/`.

### 2) Fix ABI mismatch for `lite3_bytes`

- [x] Update the Cython `lite3_bytes` definition to match upstream (`gen`, `len`, `ptr`).
  - Target: `src/pylite3.pyx`.
- [x] Add a test that uses bytes fields to ensure correctness stays intact.
  - Target: `tests/`.

### 3) Make buffer ownership/pinning robust

- [x] Stop relying on a raw pointer after releasing `Py_buffer`; retain a stable owner (e.g., keep a `memoryview`/pinned export) so pointers don’t dangle with mutable buffers.
  - Target: `src/pylite3.pyx` (`Lite3Object.__init__`).
- [x] Add explicit tests for `bytearray` and `memoryview` inputs (and ensure behavior is deterministic).
  - Target: `tests/`.

### 4) Strengthen `loads()` validation for untrusted bytes

- [x] Call lite3’s verification routine (e.g. `_lite3_verify_get`) in `loads()` before constructing proxies for arbitrary bytes.
  - Target: `src/pylite3.pyx` (`loads`).
- [x] Add tests for malformed buffers where the first byte looks valid but the structure is invalid (must raise cleanly, never crash).
  - Target: `tests/`.

### 5) Fix object key iteration correctness

- [x] Stop using `strlen(key.ptr)`; use `key.len` and/or safe access patterns consistent with upstream `LITE3_STR` guidance.
  - Target: `src/pylite3.pyx` (`_iter_gen`).
- [x] Add a test that ensures keys with embedded `\\0` are handled consistently (if lite3 allows them) or rejected deterministically.
  - Target: `tests/`.

## Phase 2 — Performance

### 6) Improve array iteration

- [x] Avoid `for i in range(len(self)): self[i]` for arrays; iterate using lite3 iterators directly to prevent repeated lookups and proxy churn.
  - Target: `src/pylite3.pyx` (`__iter__` / `_iter_gen`).

### 7) Make `dumps()` buffer sizing dynamic

- [x] Replace fixed 64MB allocation with a growable strategy (start small, grow on “no space” failures).
  - Target: `src/pylite3.pyx` (`dumps`, writer helpers).
- [x] Add microbench/regression test that ensures `dumps({\"a\":1})` doesn’t allocate tens of MB.
  - Target: `tests/` (or `examples/` if tests shouldn’t assert perf).

### 8) Reduce proxy allocations in `to_python()`

- [x] When iterating objects/arrays for recursive conversion, materialize scalars directly (avoid creating `Lite3Object` wrappers for every scalar).
  - Target: `src/pylite3.pyx` (`to_python`, `_iter_gen`).

## Phase 3 — API ergonomics

### 9) Add dict-like convenience methods

- [x] Add `Lite3Object.get(key, default=None)` for object types.
- [x] Add fast `__contains__` for objects using `lite3_get_type` (avoid O(n) key iteration).
  - Target: `src/pylite3.pyx`.

### 10) Array indexing improvements

- [x] Support negative indices for arrays (`obj[-1]` etc.).
  - Target: `src/pylite3.pyx`.

### 11) Clarify `dumps()` return type

- [x] Decide whether to keep `bytes | str` return type or introduce `dumps_json()` / `fallback=` mode for less surprising behavior.
  - Target: `src/pylite3.pyx`, `src/pylite3/__init__.pyi`, docs.

## Phase 4 — Tests + quality gates

- [x] Add a “malformed lite3 corpus” test file(s) (small hand-crafted bytes) ensuring safe rejection.
- [x] Add CI-only fuzz-ish test (bounded) to catch crashes/regressions (optional).
- [x] Consider adding `python -m pip install build` + `python -m build` parity check (decided unnecessary; `uv build` already covers this).

## Phase 5 — Docs + release notes

- [x] Document binary format expectations: `loads()` accepts lite3 bytes; JSON bytes go through fallback.
- [x] Document `dumps()` behavior (when it returns bytes vs JSON string) and any new flags introduced.
- [x] Add a brief “Compatibility” section (CPython only, supported OS/architectures via wheels).
