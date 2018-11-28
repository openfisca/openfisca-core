# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import argparse
import logging
import sys
import os
import warnings

from openfisca_core.tools.test_runner import run_tests
from openfisca_core.scripts import add_tax_benefit_system_arguments, build_tax_benefit_system


def build_parser(parser):
    parser.add_argument('path', help = "paths (files or directories) of tests to execute", nargs = '+')
    parser = add_tax_benefit_system_arguments(parser)
    parser.add_argument('-n', '--name_filter', default = None, help = "partial name of tests to execute. Only tests with the given name_filter in their name, file name, or keywords will be run.")
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    parser.add_argument('-o', '--only-variables', nargs = '*', default = None, help = "variables to test. If specified, only test the given variables.")
    parser.add_argument('-i', '--ignore-variables', nargs = '*', default = None, help = "variables to ignore. If specified, do not test the given variables.")

    return parser


def main(parser = None):
    if not parser:
        parser = argparse.ArgumentParser()
        parser = build_parser(parser)

        warnings.warn("The 'openfisca-run-test' command has been deprecated in favor of 'openfisca test' since version 25.0, and will be removed in the future.",
            Warning
            )

    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

    tax_benefit_system = build_tax_benefit_system(args.country_package, args.extensions, args.reforms)

    options = {
        'verbose': args.verbose,
        'name_filter': args.name_filter,
        'only_variables': args.only_variables,
        'ignore_variables': args.ignore_variables,
        }

    paths = map(os.path.abspath, args.path)
    tests_ok = run_tests(tax_benefit_system, paths, options)

    if not tests_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
