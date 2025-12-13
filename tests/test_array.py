
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

def test_array_slicing(parser):
    """Ensure slicing works."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    
    assert doc[0:2] == [0, 1]
    assert doc[::2] == [0, 2, 4]
    assert doc[4:] == [4, 5]

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
    # Now that object iteration works, this should SUCCEED.
    
    lst = doc.as_list()
    assert lst == [1, [2, 3], {"a": 4}]
         
    # However, we CAN iterate and access the subarray
    sub = doc[1]
    assert sub.is_array
    assert sub.as_list() == [2, 3]

