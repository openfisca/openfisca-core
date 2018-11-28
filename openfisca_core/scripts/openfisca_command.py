from __future__ import unicode_literals, print_function, division, absolute_import
import argparse
import sys

from openfisca_web_api.scripts.serve import build_parser as build_serve_parser, main as serve
from openfisca_core.scripts.run_test import build_parser as build_test_parser, main as run_test


"""
    Define the `openfisca` command line interface.
"""


def get_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help = 'Available commands', dest = 'command')
    subparsers.required = True  # Can be added as an argument of add_subparsers in Python 3

    parser_serve = subparsers.add_parser('serve', help = 'Run the OpenFisca Web API')
    parser_serve = build_serve_parser(parser_serve)

    parser_test = subparsers.add_parser('test', help = 'Run OpenFisca YAML tests')
    parser_test = build_test_parser(parser_test)

    return parser


def main():
    parser = get_parser()

    args, _ = parser.parse_known_args()

    if args.command == 'serve':
        return sys.exit(serve(parser))
    if args.command == 'test':
        return sys.exit(run_test(parser))


if __name__ == '__main__':
    sys.exit(main())
