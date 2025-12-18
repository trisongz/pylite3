# Usage

## Quickstart

```python
import pylite3

data = pylite3.dumps({"users": [{"id": 1, "name": "Ada"}]})
obj = pylite3.loads(data)

print(obj["users"][0]["name"])  # "Ada"
```

## `loads()` behavior

`pylite3.loads(data)` is designed to behave like `json.loads`, but with a fast-path:

- If `data` is **valid Lite3 bytes**, it returns a lazy `Lite3Object` proxy (unless `recursive=True`).
- Otherwise, it **falls back to** `json.loads(...)`.

Supported Lite3 inputs include `bytes`, `bytearray`, and `memoryview`.

```python
import json
import pylite3

json_bytes = b'{"a": 1, "b": [1, 2, 3]}'

# Not Lite3 -> fallback to json.loads -> returns dict
assert pylite3.loads(json_bytes) == {"a": 1, "b": [1, 2, 3]}

# Convert JSON -> Lite3 explicitly
lite3_bytes = pylite3.dumps(json.loads(json_bytes), fallback="raise")
obj = pylite3.loads(lite3_bytes)
assert obj["b"][0] == 1
```

## `Lite3Object` basics

### Objects (dict-like)

```python
obj = pylite3.loads(pylite3.dumps({"a": 1, "b": 2}))

assert len(obj) == 2
assert "a" in obj
assert obj.get("missing", 123) == 123

for k in obj:
    print(k)  # keys
```

### Arrays (list-like)

```python
arr = pylite3.loads(pylite3.dumps([10, 20, 30]))

assert arr[0] == 10
assert arr[-1] == 30
assert arr[0:2] == [10, 20]

for v in arr:
    print(v)
```

### Recursive conversion

```python
data = pylite3.dumps({"a": [1, {"b": 2}]})
obj = pylite3.loads(data)

assert obj.as_dict() == {"a": [1, {"b": 2}]}
assert pylite3.loads(data, recursive=True) == {"a": [1, {"b": 2}]}
```

## `dumps()` behavior and fallback

`pylite3.dumps(...)` tries to produce Lite3 `bytes`. If Lite3 serialization fails, it falls back to `json.dumps(...)` and returns a `str` by default.

To disable fallback:

```python
import pylite3

class X: ...

try:
    pylite3.dumps({"x": X()}, fallback="raise")
except Exception:
    pass
```

Notes:
- Lite3 serialization supports: `dict`, `list`/`tuple`, `str`, `int`, `float`, `bool`, `None`, `bytes`.
- Root must be a `dict` or `list`/`tuple` for Lite3 encoding.
- Object keys must be `str` and must not contain NUL (`"\0"`).

