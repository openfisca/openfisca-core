# -*- coding: utf-8 -*-

import importlib
import logging
import pkgutil
import sys

from openfisca_core.reforms import Reform

log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s')


def handle_error(error_message):
    log.error(error_message)
    sys.exit(1)


def add_tax_benefit_system_arguments(parser):
    parser.add_argument('-c', '--country_package', action = 'store', help = u'country package to use. If not provided, an automatic detection will be attempted by scanning the python packages installed in your environment which name contains the word "openfisca".')
    parser.add_argument('-e', '--extensions', action = 'store', help = u'extensions to load', nargs = '*')
    parser.add_argument('-r', '--reforms', action = 'store', help = u'reforms to apply to the country package', nargs = '*')

    return parser


def build_tax_benefit_sytem(country_package_name, extensions, reforms):
    if country_package_name is None:
        country_package_name = detect_country_package()
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        handle_error(u'Could not import module `{}`. Make sure it is installed in your environment.'.format(country_package_name))
    if not hasattr(country_package, 'CountryTaxBenefitSystem'):
        handle_error(u'`{}` does not seem to be a valid Openfisca country package.'.format(country_package_name))

    country_package = importlib.import_module(country_package_name)
    tax_benefit_system = country_package.CountryTaxBenefitSystem()

    if extensions:
        for extension in extensions:
            tax_benefit_system.load_extension(extension)

    if reforms:
        for reform_path in reforms:
            try:
                reform_package, reform_name = reform_path.rsplit('.', 1)
            except ValueError:
                handle_error(u'`{}` does not seem to be a path pointing to a reform. A path looks like `some_country_package.reforms.some_reform.`'.format(reform_path))
            try:
                reform_module = importlib.import_module(reform_package)
            except ImportError:
                handle_error(u'Could not import `{}`.'.format(reform_package))
            reform = getattr(reform_module, reform_name, None)
            if reform is None:
                handle_error(u'{} has no attribute {}'.format(reform_package, reform_name))
            if not isinstance(reform, Reform):
                handle_error(u'`{}` does not seem to be a valid Openfisca reform for `{}`.'.format(reform_path, country_package.__name__))
            tax_benefit_system = reform(tax_benefit_system)

    return tax_benefit_system


def detect_country_package():
    installed_country_packages = []
    for module_description in pkgutil.iter_modules():
        module_name = module_description[1]
        if 'openfisca' in module_name.lower():
            module = importlib.import_module(module_name)
            if hasattr(module, 'CountryTaxBenefitSystem'):
                installed_country_packages.append(module_name)

    if len(installed_country_packages) == 0:
        handle_error(u'No country package has been detected on your environment. If your country package is installed but not detected, please use the --country_package option.')
    if len(installed_country_packages) > 1:
        log.warning(u'Several country packages detected : `{}`. Using `{}` by default. To use another package, please use the --country_package option.'.format(', '.join(installed_country_packages), installed_country_packages[0]))
    return installed_country_packages[0]
