
import pytest
import pylite3
import json

def test_loads_fallback_string(parser):
    """
    Test that loads() handles string input by falling back to json.loads.
    """
    json_str = '{"key": "value"}'
    
    # This should work via fallback
    obj = pylite3.loads(json_str)
    
    assert isinstance(obj, dict)
    assert obj == {"key": "value"}

def test_loads_fallback_json_bytes(parser):
    """
    Test that loads() handles standard JSON bytes (that aren't valid lite3) by falling back.
    Note: Lite3 bytes start with a type tag. "{" (0x7B) is technically LITE3_TYPE_INVALID (if we map it)
    or just outside range.
    Our implementation of `is_valid` checks `_type_cache <= LITE3_TYPE_ARRAY`.
    0x7B is 123. 123 > 7. So it should be invalid.
    """
    json_bytes = b'{"key": "value"}'
    
    obj = pylite3.loads(json_bytes)
    
    assert isinstance(obj, dict)
    assert obj == {"key": "value"}

def test_dumps_fallback_unsupported_type():
    """
    Test that dumps() uses json fallback for unsupported types (if json supports them via default? 
    Impl defined, but here we test standard fallback).
    Actually, let's test a simple int root. 
    pylite3.dumps logic requires root to be dict or list.
    json.dumps supports int root.
    """
    val = 12345
    
    # pylite3.dumps normal logic raises TypeError for int root.
    # Fallback should catch it and use json.dumps
    
    res = pylite3.dumps(val)
    
    assert res == "12345" # json.dumps returns str

def test_dumps_fallback_kwargs():
    """
    Test that kwargs are passed to fallback.
    We force fallback by using an unsupported type or by explicitly triggering it?
    Or maybe we can't easily force fallback for valid dicts unless we sabotage it.
    
    But wait, if we pass `indent=2` to dumps, existing logic ignores it and returns lite3 bytes.
    UNLESS we deliberately check for kwargs?
    Our implementation: tries lite3 first. If it succeeds, it returns bytes.
    If it fails, it returns json.
    
    So `pylite3.dumps({"a":1}, indent=2)` will return LITE3 BINARY (indent ignored).
    This is what we decided in the plan ("Attempt lite3... On failure, return json").
    """
    # To test fallback kwargs, we need an input that FAILS lite3 but PASSES json.
    # We use non-string keys, which Lite3 enforces but JSON (python module) allows (by converting to string).
    # wait, python json dumps: {1: 2} -> "{\"1\": 2}".
    # Lite3: TypeError. Fallback happens.
    
    obj = {1: "custom"} 
    
    # We pass 'indent' kwarg, which only JSON uses.
    res = pylite3.dumps(obj, indent=2)
    
    # json.dumps output for {1: "custom"} with indent=2
    # keys are sorted by default in json.dumps? No, only if sort_keys=True.
    # But usually it's insertion order.
    # space after separator is default.
    assert res == '{\n  "1": "custom"\n}'
