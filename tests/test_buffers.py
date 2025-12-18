import pytest
import pylite3


def test_loads_accepts_bytearray_and_memoryview():
    data = pylite3.dumps({"a": 1, "b": [1, 2, 3], "c": {"x": "y"}, "blob": b"hi"})
    assert isinstance(data, (bytes, bytearray))

    ba = bytearray(data)
    mv = memoryview(ba)

    obj1 = pylite3.loads(ba, recursive=True)
    obj2 = pylite3.loads(mv, recursive=True)

    assert obj1 == {"a": 1, "b": [1, 2, 3], "c": {"x": "y"}, "blob": b"hi"}
    assert obj2 == obj1


def test_loads_rejects_truncated_object_tag():
    # 6 == LITE3_TYPE_OBJECT (see enum in src/pylite3.pyx)
    # This is not a valid lite3 object; it should fail cleanly (no crash).
    data = bytes([6])
    with pytest.raises(Exception):
        pylite3.loads(data)
