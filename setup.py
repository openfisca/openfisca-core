#! /usr/bin/env python

from __future__ import annotations

from typing import List

import re
from pathlib import Path
from setuptools import setup, find_packages


def load_requirements_from_file(filename: str) -> List[str]:
    """Allows for composable requirement files with the `-r filename` flag."""

    file = Path(f"./requirements/{filename}").resolve()
    reqs = open(file).readlines()
    pattern = re.compile(r"^\s*-r\s*(?P<filename>.*)$")

    for req in reqs:
        match = pattern.match(req)

        if match:
            reqs.remove(req)
            reqs.extend(load_requirements_from_file(match.group("filename")))

    return reqs


setup(
    name = 'OpenFisca-Core',
    version = '36.0.0',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.org',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ],
    description = 'A versatile microsimulation free software',
    keywords = 'benefit microsimulation social tax',
    license = 'https://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://github.com/openfisca/openfisca-core',
    data_files = [
        (
            'share/openfisca/openfisca-core',
            ['CHANGELOG.md', 'LICENSE', 'README.md'],
            ),
        ],
    entry_points = {
        'console_scripts': [
            'openfisca=openfisca_core.scripts.openfisca_command:main',
            'openfisca-run-test=openfisca_core.scripts.openfisca_command:main',
            ],
        },
    python_requires = ">= 3.7",
    install_requires = load_requirements_from_file("install"),
    extras_require = {
        "common": load_requirements_from_file("common"),
        "coverage": load_requirements_from_file("coverage"),
        "dev": load_requirements_from_file("dev"),
        "publication": load_requirements_from_file("publication"),
        "tracker": load_requirements_from_file("tracker"),
        "web-api": load_requirements_from_file("web-api"),
        },
    include_package_data = True,  # Will read MANIFEST.in
    packages = find_packages(exclude=['tests*']),
    )
