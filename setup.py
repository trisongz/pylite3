from setuptools import setup, Extension
from Cython.Build import cythonize
import os
import subprocess
from pathlib import Path


def _ensure_lite3_submodule_checked_out() -> None:
    """
    Ensure `vendor/lite3` sources exist when building from a git checkout.

    A plain `git clone` does not fetch submodules by default, but our extension
    build requires `vendor/lite3/src/lite3.c` and headers to exist.
    """
    repo_root = Path(__file__).resolve().parent
    required_src = repo_root / "vendor" / "lite3" / "src" / "lite3.c"

    if required_src.exists():
        return

    # If we're not in a git checkout, we can't initialize submodules here.
    if not (repo_root / ".git").exists():
        raise RuntimeError(
            "Missing lite3 sources at vendor/lite3. If you cloned from git, run:\n"
            "  git submodule update --init --recursive\n"
            "Or clone with:\n"
            "  git clone --recurse-submodules <repo>\n"
        )

    if os.environ.get("PYLITE3_SKIP_SUBMODULE_UPDATE") == "1":
        raise RuntimeError(
            "Missing lite3 sources at vendor/lite3 and submodule auto-update is disabled "
            "(PYLITE3_SKIP_SUBMODULE_UPDATE=1). Run:\n"
            "  git submodule update --init --recursive\n"
        )

    try:
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=str(repo_root),
            check=True,
        )
    except Exception as e:
        raise RuntimeError(
            "Failed to initialize the lite3 submodule. Run:\n"
            "  git submodule update --init --recursive\n"
        ) from e

    if not required_src.exists():
        raise RuntimeError(
            "lite3 submodule update completed but vendor/lite3/src/lite3.c is still missing."
        )

# Check for coverage/tracing build
use_tracing = os.environ.get("CYTHON_TRACE") == "1"

macros = []
compiler_directives = {'language_level': "3"}

if use_tracing:
    macros.append(("CYTHON_TRACE", "1"))
    macros.append(("CYTHON_TRACE_NOGIL", "1"))
    compiler_directives['linetrace'] = True

# Ensure vendored C sources exist for builds from git.
_ensure_lite3_submodule_checked_out()

# Define the C Extension
extensions = [
    Extension(
        name="pylite3",
        sources=[
            "src/pylite3.pyx",
            "vendor/lite3/src/lite3.c"  # Compile the C lib alongside the binding
        ],
        include_dirs=["vendor/lite3/include"],
        define_macros=macros,
        # Optimization flags (adjust for GCC/Clang vs MSVC)
        extra_compile_args=["-O3", "-std=c11", "-march=native"],
    )
]

setup(
    ext_modules=cythonize(
        extensions, 
        compiler_directives=compiler_directives
    ),
    include_package_data=True,
)
