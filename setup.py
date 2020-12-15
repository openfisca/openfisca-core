#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.

general_requirements = [
    'dpath >= 1.5.0, < 2.0.0',
    'pytest >= 4.4.1, < 6.0.0',  # For openfisca test
    'numpy >= 1.11, < 1.19',
    'psutil >= 5.4.7, < 6.0.0',
    'PyYAML >= 3.10',
    'sortedcontainers == 2.2.2',
    'numexpr >= 2.7.0, <= 3.0',
    ]

api_requirements = [
    'werkzeug >= 1.0.0, < 2.0.0',
    'flask == 1.1.2',
    'flask-cors == 3.0.7',
    'gunicorn >= 20.0.0, < 21.0.0',
    ]

dev_requirements = [
    'autopep8 >= 1.4.0, < 1.6.0',
    'flake8 >= 3.7.0, < 3.9.0',
    'flake8-bugbear >= 19.3.0, < 20.0.0',
    'flake8-print >= 3.1.0, < 4.0.0',
    'pytest-cov >= 2.6.1, < 3.0.0',
    'mypy >= 0.701, < 0.800',
    'openfisca-country-template >= 3.10.0, < 4.0.0',
    'openfisca-extension-template >= 1.2.0rc0, < 2.0.0'
    ] + api_requirements

setup(
    name = 'OpenFisca-Core',
    version = '35.0.0',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.org',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ],
    description = 'A versatile microsimulation free software',
    keywords = 'benefit microsimulation social tax',
    license = 'https://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://github.com/openfisca/openfisca-core',

    data_files = [
        ('share/openfisca/openfisca-core', ['CHANGELOG.md', 'LICENSE', 'README.md']),
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
    message_extractors = {
        'openfisca_core': [
            ('**.py', 'python', None),
            ],
        },
    packages = find_packages(exclude=['tests*']),
    )
