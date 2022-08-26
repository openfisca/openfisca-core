import argparse
import warnings
import sys

from openfisca_core.scripts import add_tax_benefit_system_arguments
"""
    Define the `openfisca` command line interface.
"""


def get_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help = 'Available commands', dest = 'command')
    subparsers.required = True  # Can be added as an argument of add_subparsers in Python 3

    def build_serve_parser(parser):
        # Define OpenFisca modules configuration
        parser = add_tax_benefit_system_arguments(parser)

        # Define server configuration
        parser.add_argument('-p', '--port', action = 'store', help = "port to serve on (use --bind to specify host and port)", type = int)
        parser.add_argument('--tracker-url', action = 'store', help = "tracking service url", type = str)
        parser.add_argument('--tracker-idsite', action = 'store', help = "tracking service id site", type = int)
        parser.add_argument('--tracker-token', action = 'store', help = "tracking service authentication token", type = str)
        parser.add_argument('--welcome-message', action = 'store', help = "welcome message users will get when visiting the API root", type = str)
        parser.add_argument('-f', '--configuration-file', action = 'store', help = "configuration file", type = str)

        return parser

    parser_serve = subparsers.add_parser('serve', help = 'Run the OpenFisca Web API')
    parser_serve = build_serve_parser(parser_serve)

    def build_test_parser(parser):
        parser.add_argument('path', help = "paths (files or directories) of tests to execute", nargs = '+')
        parser = add_tax_benefit_system_arguments(parser)
        parser.add_argument('-n', '--name_filter', default = None, help = "partial name of tests to execute. Only tests with the given name_filter in their name, file name, or keywords will be run.")
        parser.add_argument('-p', '--pdb', action = 'store_true', default = False, help = "drop into debugger on failures or errors")
        parser.add_argument('--performance-graph', '--performance', action = 'store_true', default = False, help = "output a performance graph in a 'performance_graph.html' file")
        parser.add_argument('--performance-tables', action = 'store_true', default = False, help = "output performance CSV tables")
        parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity. If specified, output the entire calculation trace.")
        parser.add_argument('-a', '--aggregate', action = 'store_true', default = False, help = "increase output verbosity to aggregate. If specified, output the avg, max, and min values of the calculation trace. This flag has no effect without --verbose.")
        parser.add_argument('-d', '--max-depth', type = int, default = None, help = "set maximal verbosity depth. If specified, output the calculation trace up to the provided depth. This flag has no effect without --verbose.")
        parser.add_argument('-o', '--only-variables', nargs = '*', default = None, help = "variables to test. If specified, only test the given variables.")
        parser.add_argument('-i', '--ignore-variables', nargs = '*', default = None, help = "variables to ignore. If specified, do not test the given variables.")

        return parser

    parser_test = subparsers.add_parser('test', help = 'Run OpenFisca YAML tests')
    parser_test = build_test_parser(parser_test)

    return parser


def main():
    if sys.argv[0].endswith('openfisca-run-test'):
        sys.argv[0:1] = ['openfisca', 'test']
        message = "The 'openfisca-run-test' command has been deprecated in favor of 'openfisca test' since version 25.0, and will be removed in the future."
        warnings.warn(message, Warning)

    parser = get_parser()

    args, _ = parser.parse_known_args()

    if args.command == 'serve':
        from openfisca_web_api.scripts.serve import main
        return sys.exit(main(parser))
    if args.command == 'test':
        from openfisca_core.scripts.run_test import main
        return sys.exit(main(parser))


if __name__ == '__main__':
    sys.exit(main())
