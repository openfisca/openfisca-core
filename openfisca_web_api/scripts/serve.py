# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import sys
import logging
import argparse

from openfisca_core.scripts import add_tax_benefit_system_arguments, build_tax_benefit_system
from openfisca_web_api.app import create_app
from openfisca_web_api.errors import handle_import_error

try:
    from gunicorn.app.base import BaseApplication
    from gunicorn.six import iteritems
    from gunicorn import config
except ImportError as error:
    handle_import_error(error)


"""
    Define the `openfisca serve` command line interface.
"""

DEFAULT_PORT = '5000'
HOST = '127.0.0.1'
DEFAULT_WORKERS_NUMBER = '3'
DEFAULT_TIMEOUT = 120


log = logging.getLogger(__name__)


def define_command_line_options(parser):
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


def read_user_configuration(default_configuration, command_line_parser):
    configuration = default_configuration
    args, unknown_args = command_line_parser.parse_known_args()

    if args.configuration_file:
        file_configuration = {}
        with open(args.configuration_file, "r") as file:
            exec(file.read(), {}, file_configuration)

        # Configuration file overloads default configuration
        update(configuration, file_configuration)

    # Command line configuration overloads all configuration
    gunicorn_parser = config.Config().parser()
    configuration = update(configuration, vars(args))
    configuration = update(configuration, vars(gunicorn_parser.parse_args(unknown_args)))
    if configuration['args']:
        command_line_parser.print_help()
        log.error('Unexpected positional argument {}'.format(configuration['args']))
        sys.exit(1)

    return configuration


def update(configuration, new_options):
    for key, value in new_options.items():
        if value is not None:
            configuration[key] = value
            if key == "port":
                configuration['bind'] = configuration['bind'][:-4] + str(configuration['port'])
    return configuration


class OpenFiscaWebAPIApplication(BaseApplication):

    def __init__(self, options):
        self.options = options
        super(OpenFiscaWebAPIApplication, self).__init__()

    def load_config(self):
        for key, value in iteritems(self.options):
            if key in self.cfg.settings:
                self.cfg.set(key.lower(), value)

    def load(self):
        tax_benefit_system = build_tax_benefit_system(
            self.options.get('country_package'),
            self.options.get('extensions'),
            self.options.get('reforms')
            )
        return create_app(
            tax_benefit_system,
            self.options.get('tracker_url'),
            self.options.get('tracker_idsite'),
            self.options.get('tracker_token'),
            self.options.get('welcome_message')
            )


def main(parser = None):
    if not parser:
        parser = argparse.ArgumentParser()
        parser = define_command_line_options(parser)

    configuration = {
        'port': DEFAULT_PORT,
        'bind': '{}:{}'.format(HOST, DEFAULT_PORT),
        'workers': DEFAULT_WORKERS_NUMBER,
        'timeout': DEFAULT_TIMEOUT,
        }
    configuration = read_user_configuration(configuration, parser)
    OpenFiscaWebAPIApplication(configuration).run()


if __name__ == '__main__':
    sys.exit(main())
