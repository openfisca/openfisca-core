# -*- coding: utf-8 -*-

import sys
import imp
import os.path
import argparse

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

from openfisca_core.scripts import add_minimal_tax_benefit_system_arguments
from ..app import create_app
from imp import load_module


DEFAULT_PORT = '5000'
DEFAULT_CONFIGURATION = {
    'bind': '127.0.0.1:{}'.format(DEFAULT_PORT),
    'workers': '3',
    }

DEFAULT_CONFIGURATION_FILE = "./server_configuration.py"


def new_configured_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--configuration_file', action = 'store', help = "read this gunicorn configuration file", type = str)
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser = add_minimal_tax_benefit_system_arguments(parser)

    parser.add_argument('--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('--tracker_idsite', action = 'store', help = "tracking service id site", type = int)

    args, unknown_args = parser.parse_known_args()

    if args.configuration_file:
        module_name = os.path.splitext(os.path.basename(args.configuration_file))[0]
        module_directory = os.path.dirname(args.configuration_file)
        module = imp.load_module(module_name, *imp.find_module(module_name, [module_directory]))

        # Make a dict out of the explicit variables in server configuration file:
        custom_configuration = [item for item in dir(module) if not item.startswith("__")]
        print custom_configuration

        # Replace/Create the relevant elements in the DEFAULT_CONFIGURATION:
        for item in custom_configuration:
            DEFAULT_CONFIGURATION[item] = getattr(module, item)
    else:
        if unknown_args:
            print u'Ignoring these unknown arguments: {}'.format(unknown_args)

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
    StandaloneApplication(app, DEFAULT_CONFIGURATION).run()


if __name__ == '__main__':
    sys.exit(main())
