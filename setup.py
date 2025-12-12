from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Check for coverage/tracing build
use_tracing = os.environ.get("CYTHON_TRACE") == "1"

macros = []
compiler_directives = {'language_level': "3"}

if use_tracing:
    macros.append(("CYTHON_TRACE", "1"))
    macros.append(("CYTHON_TRACE_NOGIL", "1"))
    compiler_directives['linetrace'] = True

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
