# API Reference

## `pylite3` Module

### `loads(data: bytes, recursive: bool = False) -> Union[Lite3Object, Any]`

Loads a lite3-encoded byte string.

- **Parameters**:
    - `data` (*bytes*): The input byte string containing valid lite3 data.
    - `recursive` (*bool*):
        - `False` (default): Returns a lazy `Lite3Object` proxy. Parsing happens only on access.
        - `True`: Immediately decodes the entire structure into standard Python objects (`dict`, `list`, `int`, etc.). *Note: Recursive loading for Objects is currently limited due to lack of key iteration in the underlying C library.*

- **Returns**: A `Lite3Object` or standard Python types.

### `dumps(obj: Union[dict, list]) -> bytes`

Serializes a Python object to lite3 bytes.

- **Parameters**:
    - `obj` (*dict | list*): The Python object to serialize. Supports nested structures and standard scalar types (`int`, `float`, `str`, `bytes`, `bool`, `None`).

- **Returns**: `bytes` containing the encoded data.

---

## `Lite3Object`

The `Lite3Object` is a lazy proxy wrapper around the underlying memory buffer. It holds a strong reference to the source data to ensure memory safety.

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

### Methods

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

#### `to_python() -> Any`

Recursively converts the value to its equivalent standard Python representation.
