from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Define the C Extension
extensions = [
    Extension(
        name="pylite3",
        sources=[
            "src/pylite3.pyx",
            "vendor/lite3/src/lite3.c"  # Compile the C lib alongside the binding
        ],
        include_dirs=["vendor/lite3/include"],
        # Optimization flags (adjust for GCC/Clang vs MSVC)
        extra_compile_args=["-O3", "-std=c11", "-march=native"],
    )
]

setup(
    ext_modules=cythonize(
        extensions, 
        compiler_directives={'language_level': "3"}
    ),
    include_package_data=True,
)
