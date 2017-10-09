# -*- coding: utf-8 -*-

import sys
import argparse
from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

import server_configuration
from openfisca_core.scripts import add_minimal_tax_benefit_system_arguments
from ..app import create_app


DEFAULT_PORT = '5000'
DEFAULT_CONFIGURATION = {
    'bind': '127.0.0.1:{}'.format(DEFAULT_PORT),
    'workers': '3',
    }

DEFAULT_CONFIGURATION_FILE = "./server_configuration.py"


def new_configured_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--configuration_file', action = 'store_true', help = "read this gunicorn configuration file: " + DEFAULT_CONFIGURATION_FILE)
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser = add_minimal_tax_benefit_system_arguments(parser)

    parser.add_argument('--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('--tracker_idsite', action = 'store', help = "tracking service id site", type = int)

    args, unknown_args = parser.parse_known_args()

    if args.configuration_file:
        # This makes a dict out of the explicit variables in server_configuration
        custom_configuration = [item for item in dir(server_configuration) if not item.startswith("__")]
        # replace/create the relevant elements in the DEFAULT_CONFIGURATION
        for item in custom_configuration:
            DEFAULT_CONFIGURATION[item] = eval('server_configuration.' + item)
        print DEFAULT_CONFIGURATION
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
