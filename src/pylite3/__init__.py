from __future__ import annotations

from importlib import metadata

from ._core import Lite3Object, dumps, loads

__all__ = ["Lite3Object", "loads", "dumps", "__version__"]


try:
    __version__ = metadata.version("pylite3")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

