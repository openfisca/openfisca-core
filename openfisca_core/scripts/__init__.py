# -*- coding: utf-8 -*-

import traceback
import importlib
import logging
import pkgutil
from os import linesep

log = logging.getLogger(__name__)


def add_tax_benefit_system_arguments(parser):
    parser.add_argument('-c', '--country-package', action = 'store', help = 'country package to use. If not provided, an automatic detection will be attempted by scanning the python packages installed in your environment which name contains the word "openfisca".')
    parser.add_argument('-e', '--extensions', action = 'store', help = 'extensions to load', nargs = '*')
    parser.add_argument('-r', '--reforms', action = 'store', help = 'reforms to apply to the country package', nargs = '*')

    return parser


def build_tax_benefit_system(country_package_name, extensions, reforms):
    if country_package_name is None:
        country_package_name = detect_country_package()
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        message = linesep.join([traceback.format_exc(),
                                'Could not import module `{}`.'.format(country_package_name),
                                'Are you sure it is installed in your environment? If so, look at the stack trace above to determine the origin of this error.',
                                'See more at <https://github.com/openfisca/country-template#installing>.'])

        raise ImportError(message)
    if not hasattr(country_package, 'CountryTaxBenefitSystem'):
        raise ImportError('`{}` does not seem to be a valid Openfisca country package.'.format(country_package_name))

    country_package = importlib.import_module(country_package_name)
    tax_benefit_system = country_package.CountryTaxBenefitSystem()

    if extensions:
        for extension in extensions:
            tax_benefit_system.load_extension(extension)

    if reforms:
        for reform_path in reforms:
            tax_benefit_system = tax_benefit_system.apply_reform(reform_path)

    return tax_benefit_system


# For retro-compatibility:
build_tax_benefit_sytem = build_tax_benefit_system


def detect_country_package():
    installed_country_packages = []
    for module_description in pkgutil.iter_modules():
        module_name = module_description[1]
        if 'openfisca' in module_name.lower():
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                message = linesep.join([traceback.format_exc(),
                                        'Could not import module `{}`.'.format(module_name),
                                        'Look at the stack trace above to determine the error that stopped installed modules detection.'])
                raise ImportError(message)
            if hasattr(module, 'CountryTaxBenefitSystem'):
                installed_country_packages.append(module_name)

    if len(installed_country_packages) == 0:
        raise ImportError('No country package has been detected on your environment. If your country package is installed but not detected, please use the --country-package option.')
    if len(installed_country_packages) > 1:
        log.warning('Several country packages detected : `{}`. Using `{}` by default. To use another package, please use the --country-package option.'.format(', '.join(installed_country_packages), installed_country_packages[0]))
    return installed_country_packages[0]
