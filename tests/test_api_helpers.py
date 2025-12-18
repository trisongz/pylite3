import pytest
import pylite3


def test_object_get_and_contains():
    data = pylite3.dumps({"a": 1})
    obj = pylite3.loads(data)

    assert "a" in obj
    assert "missing" not in obj
    assert obj.get("a") == 1
    assert obj.get("missing") is None
    assert obj.get("missing", 123) == 123


def test_array_negative_indexing():
    data = pylite3.dumps([1, 2, 3])
    arr = pylite3.loads(data)
    assert arr[-1] == 3
    assert arr[-2] == 2
    with pytest.raises(IndexError):
        _ = arr[-999]


def test_dumps_rejects_nul_in_keys():
    with pytest.raises(TypeError):
        _ = pylite3.dumps({"a\x00b": 1}, fallback="raise")
