#! /usr/bin/env python

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of our README file for PyPi
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.

general_requirements = [
    'dpath >= 1.5.0, < 3.0.0',
    'nptyping == 1.4.4',
    'numexpr >= 2.7.0, <= 3.0',
    'numpy >= 1.11, < 1.21',
    'psutil >= 5.4.7, < 6.0.0',
    'pytest >= 4.4.1, < 6.0.0',  # For openfisca test
    'PyYAML >= 3.10',
    'sortedcontainers == 2.2.2',
    'typing-extensions >= 4.0.0, < 5.0.0',
    ]

api_requirements = [
    'markupsafe == 2.0.1',  # While flask revision < 2
    'flask == 1.1.4',
    'flask-cors == 3.0.10',
    'gunicorn >= 20.0.0, < 21.0.0',
    'werkzeug >= 1.0.0, < 2.0.0',
    ]

dev_requirements = [
    'autopep8 >= 1.4.0, < 1.6.0',
    'coverage == 6.0.2',
    'darglint == 1.8.0',
    'flake8 >= 4.0.0, < 4.1.0',
    'flake8-bugbear >= 19.3.0, < 20.0.0',
    'flake8-docstrings == 1.6.0',
    'flake8-print >= 3.1.0, < 4.0.0',
    'flake8-rst-docstrings == 0.2.3',
    'mypy == 0.910',
    'openfisca-country-template >= 3.10.0, < 4.0.0',
    'openfisca-extension-template >= 1.2.0rc0, < 2.0.0',
    'pycodestyle >= 2.8.0, < 2.9.0',
    'pylint == 2.10.2',
    ] + api_requirements

setup(
    name = 'OpenFisca-Core',
    version = '35.11.1',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.org',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ],
    description = 'A versatile microsimulation free software',
    keywords = 'benefit microsimulation social tax',
    license = 'https://www.fsf.org/licensing/licenses/agpl-3.0.html',
    license_files = ("LICENSE",),
    url = 'https://github.com/openfisca/openfisca-core',
    long_description=long_description,
    long_description_content_type='text/markdown',

    data_files = [
        (
            'share/openfisca/openfisca-core',
            ['CHANGELOG.md', 'README.md'],
            ),
        ],
    entry_points = {
        'console_scripts': [
            'openfisca=openfisca_core.scripts.openfisca_command:main',
            'openfisca-run-test=openfisca_core.scripts.openfisca_command:main',
            ],
        },
    extras_require = {
        'web-api': api_requirements,
        'dev': dev_requirements,
        'tracker': [
            'openfisca-tracker == 0.4.0',
            ],
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires = general_requirements,
    packages = find_packages(exclude=['tests*']),
    )
