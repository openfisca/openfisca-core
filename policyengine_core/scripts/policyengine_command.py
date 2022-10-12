import argparse
import warnings
import sys

from policyengine_core.scripts import add_tax_benefit_system_arguments

"""
    Define the `openfisca` command line interface.
"""


def get_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        help="Available commands", dest="command"
    )
    subparsers.required = (
        True  # Can be added as an argument of add_subparsers in Python 3
    )

    def build_test_parser(parser):
        parser.add_argument(
            "path",
            help="paths (files or directories) of tests to execute",
            nargs="+",
        )
        parser = add_tax_benefit_system_arguments(parser)
        parser.add_argument(
            "-n",
            "--name_filter",
            default=None,
            help="partial name of tests to execute. Only tests with the given name_filter in their name, file name, or keywords will be run.",
        )
        parser.add_argument(
            "-p",
            "--pdb",
            action="store_true",
            default=False,
            help="drop into debugger on failures or errors",
        )
        parser.add_argument(
            "--performance-graph",
            "--performance",
            action="store_true",
            default=False,
            help="output a performance graph in a 'performance_graph.html' file",
        )
        parser.add_argument(
            "--performance-tables",
            action="store_true",
            default=False,
            help="output performance CSV tables",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="increase output verbosity. If specified, output the entire calculation trace.",
        )
        parser.add_argument(
            "-a",
            "--aggregate",
            action="store_true",
            default=False,
            help="increase output verbosity to aggregate. If specified, output the avg, max, and min values of the calculation trace. This flag has no effect without --verbose.",
        )
        parser.add_argument(
            "-d",
            "--max-depth",
            type=int,
            default=None,
            help="set maximal verbosity depth. If specified, output the calculation trace up to the provided depth. This flag has no effect without --verbose.",
        )
        parser.add_argument(
            "-o",
            "--only-variables",
            nargs="*",
            default=None,
            help="variables to test. If specified, only test the given variables.",
        )
        parser.add_argument(
            "-i",
            "--ignore-variables",
            nargs="*",
            default=None,
            help="variables to ignore. If specified, do not test the given variables.",
        )

        return parser

    def build_data_parser(parser):
        parser.add_argument("dataset", help="The dataset to focus on.")
        parser = add_tax_benefit_system_arguments(parser, country_only=True)
        parser.add_argument(
            "action",
            choices=["build", "download", "upload", "remove", "list"],
            help="The action to perform. Pass any additional options as keyword arguments.",
        )

        return parser

    parser_test = subparsers.add_parser(
        "test", help="Run OpenFisca YAML tests"
    )
    parser_test = build_test_parser(parser_test)

    parser_data = subparsers.add_parser("data", help="Manage OpenFisca data")
    parser_data = build_data_parser(parser_data)

    return parser


def main():

    parser = get_parser()

    args, _ = parser.parse_known_args()

    if args.command == "test":
        from policyengine_core.scripts.run_test import main

        return sys.exit(main(parser))

    if args.command == "data":
        from policyengine_core.scripts.run_data import main

        return sys.exit(main(parser))


if __name__ == "__main__":
    sys.exit(main())
