#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name = 'OpenFisca-Core',
    version = '22.0.3.dev0',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    description = u'A versatile microsimulation free software',
    keywords = 'benefit microsimulation social tax',
    license = 'https://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://github.com/openfisca/openfisca-core',

    data_files = [
        ('share/openfisca/openfisca-core', ['CHANGELOG.md', 'LICENSE.AGPL.txt', 'README.md']),
        ],
    entry_points = {
        'console_scripts': ['openfisca=openfisca_core.scripts.openfisca_command:main', 'openfisca-run-test=openfisca_core.scripts.run_test:main'],
        },
    extras_require = {
        'test': [
            'nose',
            'flake8 >= 3.4.0, < 3.5.0',
            'openfisca-country-template >= 2.1, < 3.0.0',
            'openfisca-extension-template >= 1.1.3, < 2.0.0',
            ],
        'tracker': [
            'openfisca-tracker == 0.2.0',
            ]
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires = [
        'Biryani[datetimeconv] >= 0.10.4',
        'numpy >= 1.11, < 1.15',
        'PyYAML >= 3.10',
        'flask == 0.12',
        'flask-cors == 3.0.2',
        'gunicorn >= 19.7.1',
        'lxml >= 3.7',
        'dpath == 1.4.0',
        'jsonschema >= 2.6',
        'enum34 >= 1.1.6',
        'psutil == 5.4.2',
        ],
    message_extractors = {
        'openfisca_core': [
            ('**.py', 'python', None),
            ],
        },
    packages = find_packages(exclude=['tests*']),
    test_suite = 'nose.collector',
    )
