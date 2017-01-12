# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import os
import importlib

from openfisca_core.tools.test_runner import run_tests
from openfisca_core.tools import detect_country_packages


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help = "paths (files or directories) of tests to execute", nargs = '+')
    parser.add_argument('-c', '--country_package', action = 'store', help = 'country package to use to run the test. If not provided, an automatic detection will be attempted by scanning the python packages installed in your environment which name contains the word "openfisca".')
    parser.add_argument('-e', '--extensions', action = 'store', help = 'extensions to load, separated by commas (e.g -e "extension_1, extension_2")')
    parser.add_argument('-r', '--reforms', action = 'store', help = 'reforms to apply to the country package, separated by commas (e.g -r openfisca_france.reforms.some_reform)')
    parser.add_argument('-f', '--force', action = 'store_true', default = False,
        help = 'force testing of tests with "ignore" flag and formulas belonging to "ignore_output_variables" list')
    parser.add_argument('-n', '--name_filter', default = None, help = "partial name of tests to execute. Only tests with the given name_filter in their name, file name, or keywords will be run.")
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    parser.add_argument('-m', '--default_relative_error_margin', help = u"relative error margin to use for tests that don't define any", action = 'store', type = float)
    parser.add_argument('-M', '--default_absolute_error_margin', help = u"absolute error margin to use for tests that don't define any", action = 'store', type = float)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

    if args.country_package:
        try:
            country_package = importlib.import_module(args.country_package)
        except:
            print('ERROR: `{}` does not seem to be a valid Openfisca country package.'.format(args.country_package))
            sys.exit(1)
    else:
        installed_country_packages = detect_country_packages()
        if len(installed_country_packages) == 0:
            print('ERROR: No country package has been detected on your environment. If your country package is installed but not detected, please use the --country_package option.')
            sys.exit(1)
        country_package_name = installed_country_packages[0]
        country_package = importlib.import_module(country_package_name)
        if len(installed_country_packages) > 1:
            print('WARNING: Several country packages detected : `{}`. Using `{}` by default. To use another package, please use the --country_package option.'.format(', '.join(installed_country_packages), country_package_name))

    tax_benefit_system = country_package.CountryTaxBenefitSystem()

    if args.extensions:
        extensions = [name.strip(' ') for name in args.extensions.split(',')]
        for extension in extensions:
            tax_benefit_system.load_extension(extension)

    if args.reforms:
        reforms = [name.strip(' ') for name in args.reforms.split(',')]
        for reform_path in reforms:
            try:
                [reform_package, reform_name] = reform_path.rsplit('.', 1)
                reform_module = importlib.import_module(reform_package)
                reform = getattr(reform_module, reform_name)
                tax_benefit_system = reform(tax_benefit_system)
            except:
                print('ERROR: `{}` does not seem to be a valid Openfisca reform for `{}`.'.format(reform_path, country_package.__name__))
                raise

    options = {
        'verbose': args.verbose,
        'force': args.force,
        'name_filter': args.name_filter,
        'default_relative_error_margin': args.default_relative_error_margin,
        'default_absolute_error_margin': args.default_absolute_error_margin,
        }

    tests_found = False

    for path in args.path:
        path = os.path.abspath(path)
        nb_tests = run_tests(tax_benefit_system, path, options)
        tests_found = tests_found or nb_tests > 0

    if not tests_found:
        print("No tests found!")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
