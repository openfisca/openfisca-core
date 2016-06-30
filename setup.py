#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name = 'OpenFisca-Core',
    version = '2.0.0',
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
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://github.com/openfisca/openfisca-core',

    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['openfisca_core/i18n/fr/LC_MESSAGES/openfisca-core.mo']),
        ('share/openfisca/openfisca-core', ['CHANGELOG.md', 'LICENSE', 'README.md']),
        ],
    extras_require = {
        'test': [
            'nose',
            ],
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires = [
        'Babel >= 0.9.4',
        'Biryani[datetimeconv] >= 0.10.4',
        'numpy >= 1.6',
        ],
    message_extractors = {
        'openfisca_core': [
            ('**.py', 'python', None),
            ],
        },
    packages = find_packages(exclude=['openfisca_core.tests*']),
    test_suite = 'nose.collector',
    )
