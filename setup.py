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

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of our README file for PyPi
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.
# DO NOT add space between '>=' and version number as it break conda build.
general_requirements = [
    "PyYAML >=6.0, <7.0",
    "dpath >=2.1.4, <3.0",
    "importlib-metadata >=6.1.0, <7.0",
    "numexpr >=2.8.4, <3.0",
    "numpy >=1.24.2, <1.25",
    "pendulum >=2.1.2, <3.0.0",
    "psutil >=5.9.4, <6.0",
    "pytest >=7.2.2, <8.0",
    "sortedcontainers >=2.4.0, <3.0",
    "typing_extensions >=4.5.0, <5.0",
    "StrEnum >=0.4.8, <0.5.0",  # 3.11.x backport
]

api_requirements = [
    "Flask >=2.2.3, < 3.0",
    "Flask-Cors >=3.0.10, < 4.0",
    "gunicorn >=20.1.0, < 21.0",
    "Werkzeug >=2.2.3, < 3.0",
]

dev_requirements = [
    "black >=23.1.0, < 24.0",
    "coverage >=6.5.0, < 7.0",
    "darglint >=1.8.1, < 2.0",
    "flake8 >=6.0.0, < 7.0.0",
    "flake8-bugbear >=23.3.23, < 24.0",
    "flake8-docstrings >=1.7.0, < 2.0",
    "flake8-print >=5.0.0, < 6.0",
    "flake8-rst-docstrings >=0.3.0, < 0.4.0",
    "idna >=3.4, < 4.0",
    "isort >=5.12.0, < 6.0",
    "mypy >=1.1.1, < 2.0",
    "openapi-spec-validator >=0.5.6, < 0.6.0",
    "pycodestyle >=2.10.0, < 3.0",
    "pylint >=2.17.1, < 3.0",
    "xdoctest >=1.1.1, < 2.0",
] + api_requirements

setup(
    name="OpenFisca-Core",
    version="40.1.0",
    author="OpenFisca Team",
    author_email="contact@openfisca.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="A versatile microsimulation free software",
    keywords="benefit microsimulation social tax",
    license="https://www.fsf.org/licensing/licenses/agpl-3.0.html",
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
            "build >=0.10.0, < 0.11.0",
            "coveralls >=3.3.1, < 4.0",
            "twine >=4.0.2, < 5.0",
            "wheel >=0.40.0, < 0.41.0",
        ],
        "tracker": ["OpenFisca-Tracker >=0.4.0, < 0.5.0"],
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=general_requirements,
    packages=find_packages(exclude=["tests*"]),
)
