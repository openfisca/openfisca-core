from __future__ import unicode_literals, print_function, division, absolute_import
import argparse
import sys

from openfisca_web_api.scripts.serve import define_command_line_options, main as serve


"""
    Define the `openfisca` command line interface.
"""


def get_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help = 'Available commands', dest = 'command')
    subparsers.required = True  # Can be added as an argument of add_subparsers in Python 3
    parser_serve = subparsers.add_parser('serve', help = 'Run the OpenFisca Web API')
    parser_serve = define_command_line_options(parser_serve)

    return parser


def main():
    parser = get_parser()
    sys.exit(serve(parser))


if __name__ == '__main__':
    sys.exit(main())
