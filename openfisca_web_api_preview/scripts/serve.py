# -*- coding: utf-8 -*-

import sys
import imp
import os.path
import logging
import argparse

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems
from gunicorn import config

from openfisca_core.scripts import add_minimal_tax_benefit_system_arguments
from openfisca_web_api_preview.app import create_app
from imp import load_module


"""
    Define the `openfisca serve` command line interface.
"""

DEFAULT_PORT = '5000'
HOST = '127.0.0.1'
DEFAULT_WORKERS_NUMBER = '3'


log = logging.getLogger(__name__)


def define_command_line_options(parser):
    # Define OpenFisca modules configuration
    parser = add_minimal_tax_benefit_system_arguments(parser)

    # Define server configuration
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser.add_argument('--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('--tracker_idsite', action = 'store', help = "tracking service id site", type = int)
    parser.add_argument('-f', '--configuration_file', action = 'store', help = "gunicorn configuration file", type = str)

    return parser


def read_user_configuration(default_configuration, command_line_parser):
    configuration = default_configuration
    args, unknown_args = command_line_parser.parse_known_args()

    if args.configuration_file:
        # Configuration file overloads default configuration
        module_name = os.path.splitext(os.path.basename(args.configuration_file))[0]
        module_directory = os.path.dirname(args.configuration_file)
        module = imp.load_module(module_name, *imp.find_module(module_name, [module_directory]))

        file_configuration = [item for item in dir(module) if not item.startswith("__")]
        for key in file_configuration:
            value = getattr(module, key)
            if value:
                configuration[key] = value
                if key == "port":
                    configuration['bind'] = configuration['bind'][:-4] + str(configuration['port'])

    # Command line configuration overloads all configuration
    gunicorn_parser = config.Config().parser()
    configuration = update(configuration, vars(args))
    configuration = update(configuration, vars(gunicorn_parser.parse_args(unknown_args)))

    return configuration


def update(configuration, new_options):
    for key in new_options:
        value = new_options[key]

        if not configuration.get(key) or value:
            configuration[key] = value
            if key == "port":
                configuration['bind'] = configuration['bind'][:-4] + str(configuration['port'])
    return configuration


class StandaloneApplication(BaseApplication):

    def __init__(self, app, options = None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        for key, value in iteritems(self.options):
            if value is None:
                log.debug('Undefined value for key `{}`.'.format(key))

            if key in self.cfg.settings and value is not None:
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

    app = create_app(configuration['country_package'], configuration['extensions'], configuration['tracker_url'], configuration['tracker_idsite'])
    StandaloneApplication(app, configuration).run()


if __name__ == '__main__':
    sys.exit(main())
