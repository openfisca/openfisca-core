# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace

import logging
import sys

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app
from openfisca_web_api.errors import handle_import_error

try:
    from gunicorn.app.base import BaseApplication
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


def create_gunicorn_parser() -> ArgumentParser:
    return config.Config().parser()


def parse_args(parser: ArgumentParser, args: list) -> dict:
    return vars(parser.parse_args(args))


def read_user_configuration(configuration, parser):
    user_args, unknown_args = parser.parse_known_args()

    if user_args.configuration_file:
        file_configuration = {}

        with open(user_args.configuration_file, "r") as file:
            exec(file.read(), {}, file_configuration)

        # Configuration file overloads default configuration
        update(configuration, file_configuration)

    # Command line configuration overloads all configuration
    gunicorn_parser = create_gunicorn_parser()
    gunicorn_args = parse_args(gunicorn_parser, unknown_args)
    configuration = update(configuration, vars(user_args))
    configuration = update(configuration, gunicorn_args)

    if configuration["args"]:
        parser.print_help()
        log.error(f"Unexpected positional argument {configuration['args']}")
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

    def __init__(self, options = {}):
        self.options = options
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
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


def main(parser):
    configuration = {
        'port': DEFAULT_PORT,
        'bind': '{}:{}'.format(HOST, DEFAULT_PORT),
        'workers': DEFAULT_WORKERS_NUMBER,
        'timeout': DEFAULT_TIMEOUT,
        }
    configuration = read_user_configuration(configuration, parser)
    OpenFiscaWebAPIApplication(configuration).run()
