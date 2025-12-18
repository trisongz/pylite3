# API Reference

## Top-level functions

### `pylite3.loads(data, *, recursive=False, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None, **kwargs)`

Behaves like `json.loads` with a Lite3 fast-path:

- If `data` is valid Lite3, returns a `Lite3Object` proxy by default.
- If `recursive=True`, returns fully materialized Python objects (`dict`/`list`/scalars).
- If `data` is not Lite3, falls back to `json.loads(...)`.

Supported Lite3 inputs include `bytes`, `bytearray`, and `memoryview`.

### `pylite3.dumps(obj, *, default=None, fallback="json", **kwargs)`

Serializes Python values into Lite3 bytes when possible.

- On success: returns `bytes` (Lite3-encoded).
- On failure:
  - `fallback="json"` (default): returns `json.dumps(...)` as `str`.
  - `fallback="raise"`: raises the original exception.

Lite3 encoding supports (native): `dict`, `list`/`tuple`, `str`, `int`, `float`, `bool`, `None`, `bytes`.

Notes:
- Root must be a `dict` or `list`/`tuple` for Lite3 encoding.
- Object keys must be `str` and must not contain NUL (`"\0"`).

## `Lite3Object`

`Lite3Object` is a lazy proxy over Lite3-encoded data. It holds a reference to the underlying buffer to keep it alive and prevent unsafe mutation while the proxy exists.

### Properties

- `.is_object`, `.is_array`
- `.is_null`, `.is_bool`, `.is_int`, `.is_float`, `.is_str`, `.is_bytes`
- `.is_valid`

### Mapping-like behavior (objects)

- `len(obj)` returns key count
- `obj["key"]` returns scalars or nested `Lite3Object`
- `"key" in obj` is supported and fast
- `obj.get("key", default=None)`
- `obj.keys()`, `obj.values()`, `obj.items()`
- Iteration: `for k in obj` yields keys

### Sequence-like behavior (arrays)

- `len(arr)` returns element count
- `arr[i]` and `arr[-1]` (negative indices supported)
- `arr[1:10:2]` returns a Python `list`
- Iteration: `for v in arr` yields values

### Recursive conversion

- `obj.to_python(...)` recursively converts to standard Python structures
- `obj.as_dict()` / `obj.as_list()` are typed convenience wrappers

