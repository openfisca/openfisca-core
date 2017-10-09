# -*- coding: utf-8 -*-

import sys
import argparse
from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

from openfisca_core.scripts import add_minimal_tax_benefit_system_arguments
from ..app import create_app


DEFAULT_PORT = '5000'
BASE_CONF = {
    'bind': '%s:%s' % ('127.0.0.1', DEFAULT_PORT),
    'workers': '3',
    }

BASE_CONF_FILE = "./server_configuration.py"


def new_configured_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--configuration_file', action = 'store_true', help = "read this gunicorn configuration file: " + BASE_CONF_FILE)
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser = add_minimal_tax_benefit_system_arguments(parser)

    parser.add_argument('-u', '--tracker_url', action = 'store', help = "tracking service url", type = str)
    parser.add_argument('-s', '--tracker_idsite', action = 'store', help = "tracking service id site", type = int)

    args, unknown_args = parser.parse_known_args()

    if args.configuration_file:
        print u'Reading configuration file `{}` instead of command line configuration...'.format(BASE_CONF_FILE)
        # TODO BASE_CONF.update(BASE_CONF_FILE)
        # print BASE_CONF
    else:
        if unknown_args:
            print u'Ignoring these unknown arguments: {}'.format(unknown_args)

    app = create_app(args.country_package, args.extensions, args.tracker_url, args.tracker_idsite)
    return app, unknown_args


class StandaloneApplication(BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    app, unknown_args = new_configured_app()
    StandaloneApplication(app, BASE_CONF).run()


if __name__ == '__main__':
    sys.exit(main())
