"""Python OHLCV Library."""

from __future__ import annotations

import setuptools


DOCLINES = __doc__.split("\n")


def get_requirements(file_path: str) -> list[str]:
    with open(file_path, "r") as file:
        package_list = file.readlines()
        package_list = [package.rstrip() for package in package_list]

    return package_list


setuptools.setup(
    name="ohlcv",
    description=DOCLINES[0],
    author="Arbyn Acosta Argabioso",
    version="0.7.1",

    install_requires=get_requirements("requirements/base.txt"),
    packages=setuptools.find_namespace_packages(include=[
        "trading.*",
    ]),
    python_requires=">=3.7"
)
