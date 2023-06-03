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
    'PyYAML >= 3.10',
    'dpath >= 1.5.0',
    'importlib-metadata >= 4.3.0',  # Required for Python 3.7 and Flake8
    'nptyping >= 1.4.4',
    'numexpr >= 2.7.0',
    'numpy >= 1.11',
    'psutil >= 5.4.7',
    'pytest >= 4.4.1',  # For openfisca test
    'sortedcontainers >= 2.2.2',
    'typing-extensions >= 4.0.0',
    ]

api_requirements = [
    'markupsafe >= 2.0.1',  # While flask revision < 2
    'flask >= 1.1.4',
    'flask-cors >= 3.0.10',
    'gunicorn >= 20.0.0',
    'werkzeug >= 1.0.0',
    ]

dev_requirements = [
    'autopep8 >= 1.4.0',
    'coverage >= 6.0.2',
    'darglint >= 1.8.0',
    'flake8 >= 4.0.0',
    'flake8-bugbear >= 19.3.0',
    'flake8-docstrings >= 1.6.0',
    'flake8-print >= 3.1.0',
    'flake8-rst-docstrings >= 0.2.3',
    'idna >= 3.4.0',
    'isort >= 5.0.0',
    'mypy >= 0.910',
    'openapi-spec-validator >= 0.5.0',
    'pycodestyle >= 2.8.0',
    'pylint >= 2.10.2',
    'xdoctest >= 1.0.0',
    ] + api_requirements

setup(
    name = 'OpenFisca-Core',
    version = '38.0.4',
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
        'ci': [
            'build >= 0.9.0, < 1.0.0',
            'coveralls >= 3.0.0, < 4.0.0',
            'twine >= 4.0.0, < 5.0.0',
            'wheel < 1.0.0',
            ],
        'tracker': ['openfisca-tracker == 0.4.0'],
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires = general_requirements,
    packages = find_packages(exclude=['tests*']),
    )
