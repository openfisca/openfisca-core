# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import os
import importlib

from openfisca_core.tools.test_runner import run_tests
from openfisca_core.scripts import add_tax_benefit_system_arguments, detect_country_package


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help = "paths (files or directories) of tests to execute", nargs = '+')
    parser = add_tax_benefit_system_arguments(parser)
    parser.add_argument('-f', '--force', action = 'store_true', default = False,
        help = 'force testing of tests with "ignore" flag and formulas belonging to "ignore_output_variables" list')
    parser.add_argument('-n', '--name_filter', default = None, help = "partial name of tests to execute. Only tests with the given name_filter in their name, file name, or keywords will be run.")
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    parser.add_argument('-m', '--default_relative_error_margin', help = u"relative error margin to use for tests that don't define any", action = 'store', type = float)
    parser.add_argument('-M', '--default_absolute_error_margin', help = u"absolute error margin to use for tests that don't define any", action = 'store', type = float)

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


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

    tax_benefit_system = build_tax_benefit_sytem(args.country_package, args.extensions, args.reforms)

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
