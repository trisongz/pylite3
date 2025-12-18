import random

import pylite3


def _rand_scalar(rng: random.Random):
    t = rng.choice(["int", "float", "str", "bool", "none", "bytes"])
    if t == "int":
        return rng.randint(-10_000, 10_000)
    if t == "float":
        return rng.random() * 10_000
    if t == "str":
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(0, 12)))
    if t == "bool":
        return rng.choice([True, False])
    if t == "bytes":
        return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 16)))
    return None


def _rand_obj(rng: random.Random, depth: int, max_depth: int):
    if depth >= max_depth:
        return _rand_scalar(rng)

    kind = rng.choice(["dict", "list", "scalar"])
    if kind == "scalar":
        return _rand_scalar(rng)
    if kind == "list":
        return [_rand_obj(rng, depth + 1, max_depth) for _ in range(rng.randint(0, 6))]

    # dict
    out = {}
    for _ in range(rng.randint(0, 6)):
        k = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(1, 8)))
        out[k] = _rand_obj(rng, depth + 1, max_depth)
    return out


def test_fuzz_roundtrip_small_deterministic():
    rng = random.Random(0)
    for _ in range(100):
        root = _rand_obj(rng, depth=0, max_depth=4)
        # dumps only supports dict/list roots for lite3 mode; other roots fall back to json (str).
        if not isinstance(root, (dict, list)):
            continue

        data = pylite3.dumps(root, fallback="raise")
        assert isinstance(data, (bytes, bytearray))
        decoded = pylite3.loads(data, recursive=True)
        assert decoded == root

