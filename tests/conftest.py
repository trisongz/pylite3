
import pytest
import pylite3

class MockParser:
    def parse(self, data):
        # pysimdjson.parse takes bytes and returns a proxy.
        # pylite3.loads(data) does exactly that (if data is properly encoded).
        # However, the input in pysimdjson tests is JSON bytes (e.g. b'{"a":1}').
        # pylite3.loads expects LITE3-encoded bytes!
        # So I need a helper that takes JSON bytes, converts to LITE3, then loads.
        
        # Luckily, we have pylite3.dumps() which takes a python dict.
        # But the tests provide JSON *bytes*.
        # I should decode JSON to python dict first, then dump to lite3, then load.
        import json
        if isinstance(data, bytes):
            data_str = data.decode('utf-8')
        else:
            data_str = data
            
        py_obj = json.loads(data_str)
        lite3_data = pylite3.dumps(py_obj)
        return pylite3.loads(lite3_data)

@pytest.fixture
def parser():
    yield MockParser()

@pytest.fixture
def doc(parser):
    yield parser.parse(b'''{
        "array": [1, 2, 3],
        "object": {"hello": "world"},
        "int64": -1,
        "uint64": 1234567890123456789,
        "double": 1.1,
        "string": "test",
        "bool": true,
        "null_value": null
    }''')
