"""Package config file.

This file contains all package's metadata, including the current version and
its third-party dependencies.

Note:
    For integration testing, OpenFisca-Core relies on two other packages,
    listed below. Because these packages rely at the same time on
    OpenFisca-Core, adding them as official dependencies creates a resolution
    loop that makes it hard to contribute. We've therefore decided to install
    them via the task manager (`make install-test`)::

        openfisca-country-template = "*"
        openfisca-extension-template = "*"

"""
from setuptools import find_packages, setup

setup(
    data_files=[
        (
            "share/openfisca/openfisca-core",
            ["CHANGELOG.md", "README.md"],
        ),
    ],
    entry_points={
        "console_scripts": [
            "openfisca=openfisca_core.scripts.openfisca_command:main",
            "openfisca-run-test=openfisca_core.scripts.openfisca_command:main",
        ],
    },
    include_package_data=True,  # Will read MANIFEST.in
    packages=find_packages(exclude=["tests*"]),
)
