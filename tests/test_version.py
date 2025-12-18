import pylite3


def test_version_is_string():
    assert isinstance(pylite3.__version__, str)
    assert pylite3.__version__

