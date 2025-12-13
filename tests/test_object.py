
import pytest
import pylite3

def test_object_abc_mapping(parser):
    """
    Test Object interface.
    Note: Iteration is NOT supported for Objects in pylite3 yet.
    """
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')
    # assert isinstance(doc, pylite3.Lite3Object) # We rely on duck typing or we need to expose the class

    # __len__
    assert len(doc) == 3

    # __contains__ - Now iteration works, so 'in' operator should work via iteration!
    # Although inefficient (O(N)), it works.
    assert 'a' in doc
    assert 'x' in doc
    assert 'z' not in doc

    # __getitem__
    # Individual key access returns proxy objects (if recursive=False logic applied? No, MockParser uses default recursive=False)
    # Wait, MockParser uses loads(data). default is recursive=False.
    # So doc['x'] is a Lite3Object.
    
    assert doc['x'].is_object
    assert doc['c'].is_array

    # Key lookup
    assert doc['a'] == 'b'
    # doc[b'a'] -> pylite3 expects string keys in __getitem__.
    with pytest.raises(TypeError):
        _ = doc[b'a']

    with pytest.raises(KeyError):
        _ = doc['z']

    # keys(), values(), items() should now work
    assert list(doc.keys()) == ['a', 'c', 'x']
    assert len(list(doc.values())) == 3
    assert len(list(doc.items())) == 3
    
    # .get() still not defined unless we add it. 
    # But dict(doc) should work now that we support iteration and if dict uses provided methods.
    # Actually, dict(doc) uses __iter__ and __getitem__ if it's not a known sequence.
    # But if keys() is present, it might use that.
    
    # Iteration yield keys
    keys = list(doc)
    assert 'a' in keys
    assert 'c' in keys
    assert 'x' in keys
    assert len(keys) == 3
    
    # dict() conversion should work because we have __iter__ and __getitem__
    d = dict(doc)
    assert d['a'] == 'b'
    assert isinstance(d['c'], pylite3.Lite3Object) # Shallow copy by dict()

def test_object_as_dict(parser):
    """Ensure as_dict works."""
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')
    
    d = doc.as_dict()
    assert isinstance(d, dict)
    assert d['a'] == 'b'
    assert d['c'] == [0, 1, 2] # Recursive conversion
    assert d['x'] == {'f': 'z'}

def test_object_mini(parser):
    """Test JSON minifier - Not implemented in pylite3."""
    doc = parser.parse(b'{"a" : "z" }')
    # doc.mini doesn't exist
    assert not hasattr(doc, 'mini')

def test_object_pointer(parser):
    """Ensure we can access an object element by pointer - Not implemented."""
    doc = parser.parse(b'{"a" : "z" }')
    # doc.at_pointer doesn't exist
    assert not hasattr(doc, 'at_pointer')
