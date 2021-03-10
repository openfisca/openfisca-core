# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace

from errno import EINVAL
from logging import getLogger
import sys

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app
from openfisca_web_api.errors import handle_import_error

try:
    from gunicorn.app.base import BaseApplication
    from gunicorn.config import Config
except ImportError as error:
    handle_import_error(error)


"""
    Define the `openfisca serve` command line interface.
"""

DEFAULT_PORT = "5000"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_WORKERS = "3"
DEFAULT_TIMEOUT = 120

DEFAULT_CONFIG = {
    "port": DEFAULT_PORT,
    "bind": f"{DEFAULT_HOST}:{DEFAULT_PORT}",
    "workers": DEFAULT_WORKERS,
    "timeout": DEFAULT_TIMEOUT,
    }


log = getLogger(__name__)


def read_config(config: dict, user_args: dict, server_args: dict) -> dict:
    if user_args.get("configuration_file"):
        file_config: dict = {}

        with open(user_args["configuration_file"], "r") as file:
            exec(file.read(), {}, file_config)

        # Configuration file overloads default configuration
        update_config(config, file_config)

    # Command line configuration overloads all configuration
    config = update_config(config, user_args)
    config = update_config(config, server_args)

    return config


def update_config(config: dict, args: dict) -> dict:
    for key, value in args.items():
        if value is not None:
            config[key] = value
            if key == "port":
                config["bind"] = config["bind"][:-4] + str(config["port"])

    return config


class OpenFiscaWebAPIApplication(BaseApplication):

    def __init__(self, options = None):
        self.options = options or {}
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


def main(user_parser: ArgumentParser) -> None:
    known_args: Namespace
    unknown_args: list

    known_args, unknown_args = user_parser.parse_known_args()
    user_args = vars(known_args)

    server_parser = Config().parser()
    known_args = server_parser.parse_args(unknown_args)
    server_args = vars(known_args)

    config = read_config(DEFAULT_CONFIG, user_args, server_args)

    if config.get("args"):
        user_parser.print_help()
        log.error(f"\nUnexpected positional argument {config['args']}")
        sys.exit(EINVAL)

    OpenFiscaWebAPIApplication(config).run()
