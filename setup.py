#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.

general_requirements = [
    'dpath == 1.4.0',
    'enum34 >= 1.1.6',
    'nose < 2.0.0',  # For openfisca test
    'numpy >= 1.11, < 1.16',
    'psutil == 5.4.6',
    'PyYAML >= 3.10',
    'ruamel.yaml >= 0.15.80, < 0.16',
    'sortedcontainers == 1.5.9',
    'numexpr == 2.6.8',
    ]

api_requirements = [
    'flask == 1.0.2',
    'flask-cors == 3.0.2',
    'gunicorn >= 19.7.1',
    ]

dev_requirements = [
    'autopep8 >= 1.4.0, < 1.5.0',
    'flake8 >= 3.7.0, < 3.8.0',
    'flake8-bugbear >= 19.3.0, < 20.0.0',
    'flake8-print >= 3.1.0, < 4.0.0',
    'pytest >= 4.0.0, < 5.0.0',
    'pytest-cov >= 2.0.0, < 3.0.0',
    'openfisca-country-template >= 3.6.0rc0, < 4.0.0',
    'openfisca-extension-template >= 1.2.0rc0, < 2.0.0'
    ] + api_requirements

setup(
    name = 'OpenFisca-Core',
    version = '32.0.0',
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
        'console_scripts': ['openfisca=openfisca_core.scripts.openfisca_command:main', 'openfisca-run-test=openfisca_core.scripts.openfisca_command:main'],
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
    test_suite = 'nose.collector',
    )
