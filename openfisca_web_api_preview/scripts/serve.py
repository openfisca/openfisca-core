# -*- coding: utf-8 -*-

import sys
import imp
import os.path
import argparse

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems
from gunicorn import config

from openfisca_core.scripts import add_minimal_tax_benefit_system_arguments
from ..app import create_app
from imp import load_module


DEFAULT_PORT = '5000'
gunicorn_configuration = {
    'bind': '127.0.0.1:{}'.format(DEFAULT_PORT),
    'workers': '3',
    }


def new_configured_app():
    parser = argparse.ArgumentParser()

    # Define OpenFisca modules configuration
    parser = add_minimal_tax_benefit_system_arguments(parser)
    # Define server configuration
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser.add_argument('--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('--tracker_idsite', action = 'store', help = "tracking service id site", type = int)
    parser.add_argument('-f', '--configuration_file', action = 'store', help = "gunicorn configuration file", type = str)

    # Read user configuration
    args, unknown_args = parser.parse_known_args()

    if args.configuration_file:
        module_name = os.path.splitext(os.path.basename(args.configuration_file))[0]
        module_directory = os.path.dirname(args.configuration_file)
        module = imp.load_module(module_name, *imp.find_module(module_name, [module_directory]))

        # Make a dict out of the explicit variables in server configuration file:
        custom_configuration = [item for item in dir(module) if not item.startswith("__")]

        # Gunicorn configuration file overloads default configuration
        for item in custom_configuration:
            gunicorn_configuration[item] = getattr(module, item)

    if unknown_args:
        # Command line configuration overloads all gunicorn configuration
        parser = config.Config().parser()
        gunicorn_configuration.update(vars(parser.parse_args(unknown_args)))
    print gunicorn_configuration
    app = create_app(args.country_package, args.extensions, args.tracker_url, args.tracker_idsite)
    return app, unknown_args


class StandaloneApplication(BaseApplication):

    def __init__(self, app, options = None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        for key, value in iteritems(self.options):
            if value is None:
                print u'Missing value for key `{}`.'.format(key)

            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    app, unknown_args = new_configured_app()
    StandaloneApplication(app, gunicorn_configuration).run()


if __name__ == '__main__':
    sys.exit(main())
