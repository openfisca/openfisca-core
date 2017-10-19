# -*- coding: utf-8 -*-

import sys
import logging
import argparse

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems
from gunicorn import config

from openfisca_core.scripts import add_tax_benefit_system_arguments, build_tax_benefit_system
from openfisca_web_api_preview.app import create_app


"""
    Define the `openfisca serve` command line interface.
"""

DEFAULT_PORT = '5000'
HOST = '127.0.0.1'
DEFAULT_WORKERS_NUMBER = '3'


log = logging.getLogger(__name__)


def define_command_line_options(parser):
    # Define OpenFisca modules configuration
    parser = add_tax_benefit_system_arguments(parser)

    # Define server configuration
    parser.add_argument('-p', '--port', action = 'store', help = "port to serve on", type = int)
    parser.add_argument('--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('--tracker_idsite', action = 'store', help = "tracking service id site", type = int)
    parser.add_argument('-f', '--configuration_file', action = 'store', help = "gunicorn configuration file", type = str)

    return parser


def read_user_configuration(default_configuration, command_line_parser):
    configuration = default_configuration
    args, unknown_args = command_line_parser.parse_known_args()

    if args.configuration_file:
        file_configuration = {}
        execfile(args.configuration_file, {}, file_configuration)

        # Configuration file overloads default configuration
        update(configuration, file_configuration)

    # Command line configuration overloads all configuration
    gunicorn_parser = config.Config().parser()
    configuration = update(configuration, vars(args))
    configuration = update(configuration, vars(gunicorn_parser.parse_args(unknown_args)))
    if configuration['args']:
        command_line_parser.print_help()
        print('Unexpected positional argument {}'.format(configuration['args']))
        sys.exit(1)

    return configuration


def update(configuration, new_options):
    for key, value in new_options.iteritems():
        if value is not None:
            configuration[key] = value
            if key == "port":
                configuration['bind'] = configuration['bind'][:-4] + str(configuration['port'])
    return configuration


class OpenFiscaWebAPIApplication(BaseApplication):

    def __init__(self, app, options = None):
        self.options = options or {}
        self.application = app
        super(OpenFiscaWebAPIApplication, self).__init__()

    def load_config(self):
        for key, value in iteritems(self.options):
            if key in self.cfg.settings:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main(parser = None):
    if not parser:
        parser = argparse.ArgumentParser()
        parser = define_command_line_options(parser)

    configuration = {
        'port': DEFAULT_PORT,
        'bind': '{}:{}'.format(HOST, DEFAULT_PORT),
        'workers': DEFAULT_WORKERS_NUMBER,
        }
    configuration = read_user_configuration(configuration, parser)
    tax_benefit_system = build_tax_benefit_system(configuration.get('country_package'), configuration.get('extensions'), configuration.get('reforms'))
    app = create_app(tax_benefit_system, configuration.get('tracker_url'), configuration.get('tracker_idsite'))
    OpenFiscaWebAPIApplication(app, configuration).run()


if __name__ == '__main__':
    sys.exit(main())
