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
# DO NOT add space between '>=' and version number as it break conda build.
general_requirements = [
    "PyYAML >=6.0, <7.0",
    "StrEnum >=0.4.8, <0.5.0",  # 3.11.x backport
    "dpath >=2.1.4, <3.0",
    "numexpr >=2.8.4, <3.0",
    "numpy >=1.24.2, <2.0",
    "pendulum >=3.0.0, <4.0.0",
    "psutil >=5.9.4, <6.0",
    "pytest >=8.3.3, <9.0",
    "sortedcontainers >=2.4.0, <3.0",
    "typing_extensions >=4.5.0, <5.0",
]

api_requirements = [
    "Flask >=2.2.3, <3.0",
    "Flask-Cors >=3.0.10, <4.0",
    "gunicorn >=21.0, <22.0",
    "Werkzeug >=2.2.3, <3.0",
]

dev_requirements = [
    "black >=24.8.0, <25.0",
    "coverage >=7.6.1, <8.0",
    "darglint >=1.8.1, <2.0",
    "flake8 >=7.1.1, <8.0.0",
    "flake8-bugbear >=24.8.19, <25.0",
    "flake8-docstrings >=1.7.0, <2.0",
    "flake8-print >=5.0.0, <6.0",
    "flake8-rst-docstrings >=0.3.0, <0.4.0",
    "idna >=3.10, <4.0",
    "isort >=5.13.2, <6.0",
    "mypy >=1.11.2, <2.0",
    "openapi-spec-validator >=0.7.1, <0.8.0",
    "pylint >=3.3.1, <4.0",
    "pylint-per-file-ignores >=1.3.2, <2.0",
    "pyright >=1.1.382, <2.0",
    "ruff >=0.6.7, <1.0",
    "ruff-lsp >=0.0.57, <1.0",
    "xdoctest >=1.2.0, <2.0",
    *api_requirements,
]

setup(
    name="OpenFisca-Core",
    version="42.0.4",
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
            "build >=0.10.0, <0.11.0",
            "coveralls >=4.0.1, <5.0",
            "twine >=5.1.1, <6.0",
            "wheel >=0.40.0, <0.41.0",
        ],
        "tracker": ["OpenFisca-Tracker >=0.4.0, <0.5.0"],
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=general_requirements,
    packages=find_packages(exclude=["tests*"]),
)
