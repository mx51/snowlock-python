#!/usr/bin/env python3

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise ValueError("Requires Python 3.6+")


def requires_from_file(filename: str) -> list:
    with open(filename, "r") as f:
        return [x.strip() for x in f if x.strip()]


with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="snowlock",
    use_scm_version=True,
    description="Lock management library for Snowflake.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="mx51",
    author_email="opensource@mx51.io",
    url="https://github.com/mx51/snowlock-python",
    license="Apache License 2.0",
    packages=find_packages(exclude=["tests"]),
    test_suite="tests",
    install_requires=requires_from_file("requirements.txt"),
    extras_require={
        "test": requires_from_file("requirements-test.txt"),
    },
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
