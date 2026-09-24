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

from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of our README file for PyPi
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.
general_requirements = [
    "PyYAML >=6.0, <7.0",
    "StrEnum >=0.4.8, <0.5.0",  # 3.11.x backport
    "dpath >=2.2.0, <3.0",
    "numexpr >=2.10.1, <3.0",
    # NumPy 1.24.2 supports Python 3.8 to 3.11
    # Numpy 2.0.2 supports Python 3.9 to 3.12
    # Numpy 2.1.2 supports Python 3.10 to 3.12
    "numpy >=1.24.2, <2.0; python_version < '3.11'",
    # NumPy 1.26.0 supports Python 3.9 to 3.12
    "numpy >=1.26.0, <=3; python_version <= '3.12'",
    # NumPy 2.1.0 supports Python 3.10 to 3.13
    "numpy >=2.1.0, <=3; python_version >= '3.13'",
    # NumPy 2.3.2 supports Python 3.11 to 3.14
    # "numpy >=2.3.2, <3; python_version >= '3.14'",
    "pendulum >=3.0.0, <4.0.0",
    "psutil >=5.9.4, <6.0",
    "pytest >=8.3.3, <9.0",
    "sortedcontainers >=2.4.0, <3.0",
    "typing_extensions >=4.5.0, <5.0",
]

api_requirements = [
    "Flask >=2.2.3, <4.0",
    "Flask-Cors >=3.0.10, <4.0",
    "gunicorn >=21.0, <22.0",
    "Werkzeug >=2.2.3, <4.0",
]

dev_requirements = [
    "codespell >=2.3.0, <3.0",
    "colorama >=0.4.4, <0.5",
    "mypy >=1.11.2, <2.0",
    "openapi-spec-validator >=0.7.1, <0.8.0",
    "ruff >=0.6.9, <1.0",
    *api_requirements,
]

setup(
    name="OpenFisca-Core",
    version="45.0.4",
    author="OpenFisca Team",
    author_email="contact@openfisca.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="A versatile microsimulation free software",
    keywords="benefit microsimulation social tax",
    license="License-Expression :: AGPL-3.0-or-later",
    license_files=("LICENSE",),
    url="https://github.com/openfisca/openfisca-core",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    extras_require={
        "web-api": api_requirements,
        "dev": dev_requirements,
        "ci": [
            "build >=0.10.0, <0.11.0",
            "twine >=6.0, <7.0",
            "wheel >=0.40.0, <0.41.0",
        ],
        "tracker": ["OpenFisca-Tracker >=0.4.0, <0.5.0"],
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=general_requirements,
    packages=find_packages(exclude=["tests*"]),
)
