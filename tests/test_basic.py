
import pytest
import pylite3

def test_uplift_scalars(doc):
    """Test uplifting of primitive types to their Python types."""
    # doc fixture comes from conftest.py
    assert doc['int64'] == -1
    
    # uint64 logic:
    # 18446744073709551615 is 2^64-1.
    # json.loads read it as int.
    # pylite3.dumps wrote it as... check code.
    # if > int64_max, lite3_set_i64 might interpret as wrapped negative?
    # or just raw bits?
    # Let's inspect what we get.
    expected_uint64 = 1234567890123456789
    assert doc['uint64'] == expected_uint64
    
    val = doc['double']
    assert isinstance(val, float)
    assert abs(val - 1.1) < 1e-9
    
    assert doc['string'] == 'test'
    assert doc['bool'] is True
    assert doc['null_value'] is None

def test_types(doc):
    assert isinstance(doc['string'], str)
    assert not isinstance(doc['string'], int)
    
    assert isinstance(doc['int64'], int)
    assert isinstance(doc['double'], float)
    assert isinstance(doc['bool'], bool)
    # null is None
    assert doc['null_value'] is None
    
    # Containers remain as proxies
    assert doc['object'].is_object
    assert doc['array'].is_array

