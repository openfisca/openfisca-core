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

general_requirements = [
    "PyYAML",
    "dpath",
    "importlib-metadata",
    "numexpr",
    "numpy",
    "psutil",
    "pytest",
    "sortedcontainers",
    "typing-extensions",
]

api_requirements = [
    "markupsafe",
    "flask",
    "flask-cors",
    "gunicorn",
    "werkzeug",
]

dev_requirements = [
    "black",
    "coverage",
    "darglint",
    "flake8",
    "flake8-bugbear",
    "flake8-docstrings",
    "flake8-print",
    "flake8-rst-docstrings",
    "idna",
    "isort",
    "mypy",
    "openapi-spec-validator",
    "pycodestyle",
    "pylint",
    "xdoctest",
] + api_requirements

setup(
    name="OpenFisca-Core",
    version="38.0.4",
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
            "build",
            "coveralls",
            "twine",
            "wheel",
        ],
        "tracker": ["openfisca-tracker"],
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=general_requirements,
    packages=find_packages(exclude=["tests*"]),
)
