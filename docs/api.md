```
# API Reference

## `pylite3` Module

### `dumps(obj, default=None, **kwargs)`

Serialize a Python object to `lite3` binary format.

- **Parameters**:
    - `obj` (*dict | list*): The Python object to serialize.
    - `default` (*callable*): Optional function to handle types NOT supported natively (e.g. `datetime`). Returns a serializable object or raises `TypeError`.
    - `**kwargs`: Fallback arguments passed to `json.dumps` if serialization fails (e.g. `indent`, `sort_keys`).

- **Returns**: `bytes` containing the encoded data.

### `loads(data, recursive=False, object_hook=None, ...)`

Deserialize `lite3` binary data.

- **Parameters**:
    - `data` (*bytes*): The `lite3` encoded data.
    - `recursive` (*bool*): If `True`, fully decode to Python objects immediately.
    - `object_hook`, `parse_float`, etc.: Standard `json` hooks applied during decoding (or fallback).

- **Returns**: `Lite3Object` (proxy) or decoded Python object.

---

## `Lite3Object`

The `Lite3Object` is a lazy proxy wrapper around the underlying memory buffer. It holds a strong reference to the source data to ensure memory safety.
It implements the `Mapping` protocol (for objects) and `Sequence` protocol (for arrays).

### Properties

Type checking properties to inspect the underlying data type without materializing the value:

- `.is_object` (*bool*)
- `.is_array` (*bool*)
- `.is_null` (*bool*)
- `.is_bool` (*bool*)
- `.is_int` (*bool*)
- `.is_float` (*bool*)
- `.is_str` (*bool*)
- `.is_bytes` (*bool*)
- `.is_valid` (*bool*): Checks if the buffer contains valid lite3 data.

### Methods

#### `keys() -> Iterator[str]`
Iterate over object keys.

#### `values() -> Iterator[Lite3Value]`
Iterate over values.

#### `items() -> Iterator[tuple[str, Lite3Value]]`
Iterate over (key, value) pairs.

#### `__getitem__(key: Union[str, int]) -> Union[Lite3Object, Scalar]`

Access an element by key (for objects) or index (for arrays).

- **Returns**: A new `Lite3Object` proxy (for nested types) or a native Python scalar value.
- **Raises**: `KeyError` (objects), `IndexError` (arrays), or `TypeError` (if not indexable).

#### `as_dict() -> dict`

Recursively converts the object to a standard Python `dict`.
*Raises `TypeError` if the underlying value is not an object.*

#### `as_list() -> list`

Recursively converts the array to a standard Python `list`.
*Raises `TypeError` if the underlying value is not an array.*

#### `to_python(object_hook=None, ...) -> Any`

Recursively converts the value to its equivalent standard Python representation.
Supports standard `json` load hooks: `object_hook`, `parse_float`, `parse_int`, `parse_constant`, `object_pairs_hook`.
