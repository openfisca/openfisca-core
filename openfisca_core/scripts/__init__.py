# -*- coding: utf-8 -*-

import sys
import importlib


def add_tax_benefit_system_arguments(parser):
    parser.add_argument('-c', '--country_package', action = 'store', help = 'country package to use. If not provided, an automatic detection will be attempted by scanning the python packages installed in your environment which name contains the word "openfisca".')
    parser.add_argument('-e', '--extensions', action = 'store', help = 'extensions to load', nargs = '*')
    parser.add_argument('-r', '--reforms', action = 'store', help = 'reforms to apply to the country package', nargs = '*')

    return parser


def build_tax_benefit_sytem(country_package, extensions, reforms):
    if country_package:
        try:
            country_package = importlib.import_module(country_package)
        except:
            print('ERROR: `{}` does not seem to be a valid Openfisca country package.'.format(country_package))
            sys.exit(1)
    else:
        country_package_name = detect_country_package()
        country_package = importlib.import_module(country_package_name)

    tax_benefit_system = country_package.CountryTaxBenefitSystem()

    if extensions:
        for extension in extensions:
            tax_benefit_system.load_extension(extension)

    if reforms:
        for reform_path in reforms:
            try:
                [reform_package, reform_name] = reform_path.rsplit('.', 1)
                reform_module = importlib.import_module(reform_package)
                reform = getattr(reform_module, reform_name)
                tax_benefit_system = reform(tax_benefit_system)
            except:
                print('ERROR: `{}` does not seem to be a valid Openfisca reform for `{}`.'.format(reform_path, country_package.__name__))
                raise

    return tax_benefit_system


def detect_country_package():
    import pkgutil
    from importlib import import_module

    installed_country_packages = []

    for module_description in pkgutil.iter_modules():
        module_name = module_description[1]
        if 'openfisca' in module_name.lower():
            module = import_module(module_name)
            if hasattr(module, 'CountryTaxBenefitSystem'):
                installed_country_packages.append(module_name)

    if len(installed_country_packages) == 0:
        print('ERROR: No country package has been detected on your environment. If your country package is installed but not detected, please use the --country_package option.')
        sys.exit(1)
    if len(installed_country_packages) > 1:
        print('WARNING: Several country packages detected : `{}`. Using `{}` by default. To use another package, please use the --country_package option.'.format(', '.join(installed_country_packages), installed_country_packages[0]))
    return installed_country_packages[0]
