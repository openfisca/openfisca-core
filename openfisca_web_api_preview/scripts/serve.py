# -*- coding: utf-8 -*-

import os
import sys
import argparse
from gunicorn.app.base import BaseApplication

from openfisca_core.scripts import add_tax_benefit_system_arguments, detect_country_package
from ..app import create_app


DEFAULT_PORT = '5000'
BASE_CONF = {
    'bind': '%s:%s' % ('127.0.0.1', DEFAULT_PORT),
    'workers': '3',
    'debug': 'true',
}


def new_configured_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', action = 'store', default = DEFAULT_PORT, help = "port to serve on", type = int)
    parser.add_argument('-t', '--tracker_url', action = 'store', help = "tracking service url", type = string)
    parser.add_argument('-s', '--tracker_idsite', action = 'store', help = "tracking service id site", type = int)
    parser = add_tax_benefit_system_arguments(parser)
    args = parser.parse_args()

    app = create_app(args.country_package, args.extensions, args.tracker_url, args.tracker_idsite)
    return app


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


if __name__ == '__main__':
    StandaloneApplication(new_configured_app(), BASE_CONF).run()
