
import pytest
import pylite3

def test_array_basic(parser):
    """Ensure we can access array elements."""
    obj = parser.parse(b'[1, 2, 3, 4, 5]')
    
    # __iter__
    assert list(iter(obj)) == [1, 2, 3, 4, 5]
    # __len__
    assert len(obj) == 5
    # __getitem__
    assert obj[2] == 3
    with pytest.raises(IndexError):
        _ = obj[99]

    # __contains__ relies on __iter__ usually, so it should work!
    assert 3 in obj
    assert 7 not in obj

def test_array_slicing_fail(parser):
    """Ensure slicing raises NotImplementedError as per design."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    
    with pytest.raises(NotImplementedError):
        _ = doc[0:2]

def test_array_uplift(parser):
    """Ensure we can turn our Array into a python list."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    
    lst = doc.as_list()
    assert lst == [0, 1, 2, 3, 4, 5]
    assert isinstance(lst, list)

def test_array_nested(parser):
    """Ensure recursive conversion works for arrays."""
    doc = parser.parse(b'[1, [2, 3], {"a": 4}]')
    # converting to list recursively calls to_python()
    # But element 2 is a Dict (Object). to_python() on Object fails!
    # So as_list() should fail here because it contains an object.
    
    with pytest.raises(NotImplementedError):
         doc.as_list()
         
    # However, we CAN iterate and access the subarray
    sub = doc[1]
    assert sub.is_array
    assert sub.as_list() == [2, 3]
