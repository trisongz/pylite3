
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

    # __contains__ - checks keys. But contains usually iterates?
    # collection.abc.Mapping __contains__ expects to find key.
    # If we implemented __contains__ efficiently via lookup, it would work.
    # But pylite3 does NOT implement __contains__ explicitly.
    # So Python falls back to __iter__, which raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        assert 'a' in doc

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

    # keys(), values(), items(), get() rely on iteration or generic mapping
    # Since __iter__ raises NotImplementedError, these fail.
    
    with pytest.raises(AttributeError):
        list(doc.keys())
        
    with pytest.raises(AttributeError):
        list(doc.values())

    with pytest.raises(AttributeError):
        list(doc.items())

    # .get() on Mapping uses __getitem__ check? Or __contains__?
    # Usually it's: try __getitem__, except KeyError return default.
    # So .get() MIGHT work if Mapping mixin is used?
    # BUT Lite3Object does NOT inherit from Mapping in .pyx.
    # So .get() defaults to AttributeError unless defined.
    # It is NOT defined in pylite3.pyx.
    with pytest.raises(AttributeError):
        doc.get('a')


def test_object_uplift_fail(parser):
    """Ensure as_dict fails as expected for now."""
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')
    
    with pytest.raises(NotImplementedError):
        doc.as_dict()

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
