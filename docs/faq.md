# FAQ

## Why does `loads(b"{...json...}")` return a `dict`?

Because JSON bytes are not Lite3-encoded data, so `pylite3.loads` falls back to `json.loads(...)`.

If you want Lite3 for a JSON file, load JSON first and then encode:

```python
import json
import pylite3

obj = json.loads(b'{"a": 1}')
data = pylite3.dumps(obj, fallback="raise")
```

## How do I force Lite3-only behavior?

Use `dumps(..., fallback="raise")` so it raises if Lite3 encoding fails instead of returning a JSON string.

`loads()` currently falls back to JSON for non-Lite3 inputs by design.

## Does `Lite3Object` copy the input buffer?

No. It holds a reference to the original buffer and reads values on demand (lazy materialization).

## What platforms are supported?

`pylite3` is a C extension targeting CPython 3.9+. Wheels are produced in GitHub Actions releases for Linux/macOS/Windows.

If you don’t see a wheel for your platform, you can build from source (requires a compiler).

