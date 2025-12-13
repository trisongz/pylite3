
import pytest
import pylite3
import json
from decimal import Decimal

def test_loads_object_hook():
    data = b'{"a": 1, "b": 2}'
    
    def hook(d):
        return sum(d.values())
        
    # recursive=True needed to trigger conversion and hook
    result = pylite3.loads(data, recursive=True, object_hook=hook)
    assert result == 3

def test_loads_object_pairs_hook():
    data = b'{"a": 1, "b": 2}'
    
    def hook(pairs):
        return [list(p) for p in pairs]
        
    result = pylite3.loads(data, recursive=True, object_pairs_hook=hook)
    # Order should be preserved? standard json does.
    # lite3 iterator order? It should be insertion order if lite3 preserves it?
    # lite3 is sorted keys? Or insertion order?
    # lite3 sorts keys for fast lookup. 
    # So we might get sorted keys.
    # Let's check what we get.
    # If keys are sorted, it might trigger alphabetical order.
    # 'a' comes before 'b'.
    assert result == [['a', 1], ['b', 2]]

def test_loads_parse_float():
    data = b'{"val": 1.5}'
    
    def hook(s):
        return Decimal(s)
        
    result = pylite3.loads(data, recursive=True, parse_float=hook)
    assert isinstance(result['val'], Decimal)
    assert result['val'] == Decimal("1.5")


def test_loads_parse_int():
    data = b'{"val": 10}'
    
    def hook(s):
        return float(s)
        
    result = pylite3.loads(data, recursive=True, parse_int=hook)
    assert isinstance(result['val'], float)
    assert result['val'] == 10.0

def test_dumps_default():
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            
    def default(obj):
        if isinstance(obj, Point):
            return {"__point__": True, "x": obj.x, "y": obj.y}
        raise TypeError
        
    p = Point(10, 20)
    # The root object itself CANNOT be serialized by lite3 directly because lite3 root must be dict/list.
    # So pylite3.dumps(p) would fallback to json.
    # To test native lite3 support for default hook, we must nest it.
    
    result = pylite3.dumps({"p": p}, default=default)
    assert isinstance(result, bytes)
    
    # Verify we can read it back
    obj = pylite3.loads(result, recursive=True)
    assert obj == {"p": {"__point__": True, "x": 10, "y": 20}}

def test_dumps_default_recursive():
    class Wrapper:
        def __init__(self, val):
             self.val = val

    def default(obj):
        if isinstance(obj, Wrapper):
            return obj.val
        raise TypeError
        
    def default(obj):
        if isinstance(obj, Wrapper):
            return obj.val
        raise TypeError
        
    w = Wrapper(Wrapper(10))
    result = pylite3.dumps([w], default=default) # Wrap in list
    obj = pylite3.loads(result, recursive=True)
    assert obj == [10]
