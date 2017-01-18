# -*- coding: utf-8 -*-

import importlib
import sys

def parse_coma_separated_args(input):
    if input:
        return [name.strip(' ') for name in input.split(',')]
    else:
        return []


TAX_BENEFIT_SYSTEM_OPTIONS = {
    'country_package': {
        'short': 'c',
        'help': 'country package to use. If not provided, an automatic detection will be attempted by scanning the python packages installed in your environment which name contains the word "openfisca".'
        },
    'extensions': {
        'short': 'e',
        'help': 'extensions to load, separated by commas (e.g -e "extension_1, extension_2")',
        },
    'reforms': {
        'short': 'r',
        'help': 'reforms to apply to the country package, separated by commas (e.g -r openfisca_france.reforms.some_reform)',
        }
}


def add_tax_benefit_system_arguments(parser):
    for option, properties in TAX_BENEFIT_SYSTEM_OPTIONS.iteritems():
        parser.add_argument(
            '-{}'.format(properties['short']),
            '--{}'.format(option),
            action = 'store',
            help = properties['help'])

    return parser


def detect_country_package():
    from pip import get_installed_distributions
    from setuptools import find_packages
    from importlib import import_module

    installed_country_packages = []

    for distribution in get_installed_distributions():
        if distribution.key.lower().find('openfisca') >= 0:
            packages = find_packages(distribution.location)
            main_package = packages[0]
            module = import_module(main_package)
            if hasattr(module, 'CountryTaxBenefitSystem'):
                installed_country_packages.append(main_package)

    if len(installed_country_packages) == 0:
        print('ERROR: No country package has been detected on your environment. If your country package is installed but not detected, please use the --country_package option.')
        sys.exit(1)
    if len(installed_country_packages) > 1:
        print('WARNING: Several country packages detected : `{}`. Using `{}` by default. To use another package, please use the --country_package option.'.format(', '.join(installed_country_packages), installed_country_packages[0]))
    return installed_country_packages[0]
