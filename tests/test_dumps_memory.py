import tracemalloc

import pylite3


def test_dumps_small_does_not_allocate_huge_buffers():
    tracemalloc.start()
    try:
        _ = pylite3.dumps({"a": 1})
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    # This primarily guards against the old behavior of allocating ~64MB bytearrays per call.
    assert peak < 5 * 1024 * 1024

