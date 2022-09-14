#! /usr/bin/env python

from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of our README file for PyPi
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.

general_requirements = [
    "dpath >= 2.0.0, < 3.0.0",
    "nptyping == 1.4.4",
    "numexpr >= 2.7.0, < 3.0.0",
    "numpy >= 1.18, < 1.21",
    "psutil >= 5.4.7, < 6.0.0",
    "pytest >= 5.4.2, < 6.0.0",  # For openfisca test
    "PyYAML >= 5.2.0, < 6.0.0",
    "sortedcontainers == 2.2.2",
    "typing-extensions >= 3.10.0, < 4.0.0",
    ]

api_requirements = [
    "markupsafe == 2.0.1",  # While flask revision < 2
    "flask == 1.1.4",
    "flask-cors == 3.0.10",
    "gunicorn >= 20.0.0, < 21.0.0",
    "werkzeug >= 1.0.0, < 2.0.0",
    ]

dev_requirements = [
    "autopep8 >= 1.7.0, < 2.0.0",
    "coverage >= 6.4.4, < 7.0.0",
    "darglint >= 1.8.1, < 2.0.0",
    "flake8 >= 5.0.4, < 6.0.0",
    "flake8-bugbear >= 22.9.11, < 23.0.0",
    "flake8-docstrings >= 1.6.0, < 2.0.0",
    "flake8-print >= 5.0.0, < 6.0.0",
    "flake8-rst-docstrings >= 0.2.7, < 1.0.0",
    "isort >= 5.10.1, < 6.0.0",
    "mypy >= 0.971, < 1.0",
    "openfisca-country-template @ git+https://github.com/openfisca/country-template.git@add-pylint",
    "openfisca-extension-template @ git+https://github.com/openfisca/extension-template.git@add-pylint",
    "pycodestyle >= 2.9.1, < 3.0.0",
    "pylint >= 2.15.2, < 3.0.0",
    "pylint-pytest >= 1.1.2, < 2.0.0",
    "pyupgrade >= 2.37.3, < 3.0.0",
    ] + api_requirements

setup(
    name = "OpenFisca-Core",
    version = "36.0.0",
    author = "OpenFisca Team",
    author_email = "contact@openfisca.org",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    description = "A versatile microsimulation free software",
    keywords = "benefit microsimulation social tax",
    license = "https://www.fsf.org/licensing/licenses/agpl-3.0.html",
    license_files = ["LICENSE"],
    url = "https://github.com/openfisca/openfisca-core",
    long_description = long_description,
    long_description_content_type = "text/markdown",

    data_files = [
        (
            "share/openfisca/openfisca-core",
            ["CHANGELOG.md", "README.md"],
            ),
        ],
    entry_points = {
        "console_scripts": [
            "openfisca=openfisca_core.scripts.openfisca_command:main",
            "openfisca-run-test=openfisca_core.scripts.openfisca_command:main",
            ],
        },
    extras_require = {
        "web-api": api_requirements,
        "dev": dev_requirements,
        "tracker": ["openfisca-tracker == 0.4.0"],
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires = general_requirements,
    packages = find_packages(exclude = ["tests*"]),
    )
