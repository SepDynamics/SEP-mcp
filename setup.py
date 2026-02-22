import os
from setuptools import setup, Extension

try:
    import pybind11

    include_dirs = [pybind11.get_include(), "src/core"]
except ImportError:
    include_dirs = ["src/core"]

ext_modules = [
    Extension(
        "manifold_engine",
        [
            "src/core/structural_entropy.cpp",
            "src/core/byte_stream_manifold.cpp",
            "src/core/bindings.cpp",
        ],
        include_dirs=include_dirs,
        language="c++",
        extra_compile_args=["-O3", "-Wall", "-shared", "-std=c++20", "-fPIC"],
        extra_link_args=["-ltbb"],
    ),
]

setup(
    name="structural-manifold-compression",
    version="0.1.0",
    description="Manifold Engine Python Bindings",
    ext_modules=ext_modules,
)
