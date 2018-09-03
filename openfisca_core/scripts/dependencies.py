#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from openfisca_core.scripts import add_tax_benefit_system_arguments, build_tax_benefit_system
from openfisca_web_api.loader import build_data
import argparse
import logging
import sys

def build_parser():
    parser = argparse.ArgumentParser()
    parser = add_tax_benefit_system_arguments(parser)
    parser.add_argument("-d", "--depth", type=int, default = 0, help="specify recursion depth (0=unlimited)")
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    parser.add_argument('-o', '--only-variables', nargs = '*', default = None, help = "variables to visit. If specified, only process the given variables.")
    parser.add_argument('-i', '--ignore-variables', nargs = '*', default = None, help = "variables to ignore. If specified, do not process the given variables.")

    return parser

def print_dependencies(data, variable_names, depth, visited):
    if depth == -1:
        return
    dependencies = set([])
    for name in variable_names:
        if name in visited:
            continue
        visited.add(name)
        if 'formulas' in data['variables'][name]:
            for key, formula in data['variables'][name]['formulas'].items():
                if formula and 'dependencies' in formula:
                    for dependency in formula['dependencies']:
                        dependencies.add(dependency)
                        print('"{}" -> "{}"'.format(name, dependency))
    if dependencies:
        print_dependencies(data, dependencies, depth - 1, visited)

def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

    tax_benefit_system = build_tax_benefit_system(args.country_package, args.extensions, args.reforms)

    wanted = args.only_variables or tax_benefit_system.variables.keys()
    ignored = args.ignore_variables or []
    variable_names = set(wanted) - set(ignored)

    data = build_data(tax_benefit_system)
    print("digraph G {")
    print_dependencies(data, variable_names, args.depth, set(ignored))
    print("}")

if __name__ == "__main__":
    sys.exit(main())
