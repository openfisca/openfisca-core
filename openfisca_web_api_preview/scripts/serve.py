# -*- coding: utf-8 -*-

import os
import sys
import argparse
from wsgiref.simple_server import make_server

from openfisca_core.scripts import add_tax_benefit_system_arguments, detect_country_package

from ..application import make_app

HOST_NAME = 'localhost'
BASE_CONF = {
    'debug': 'true',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', action = 'store', default = 2000, help = "port to serve on", type = int)
    parser = add_tax_benefit_system_arguments(parser)
    args = parser.parse_args()

    conf = BASE_CONF.copy()
    conf['country_package'] = args.country_package or detect_country_package()
    if args.extensions:
        # The api excepts the extensions and reforms to be separated by line breaks in the conf
        conf['extensions'] = os.linesep.join(args.extensions)
    if args.reforms:
        conf['reforms'] = os.linesep.join(args.reforms)

    app = make_app({}, **conf)
    httpd = make_server(HOST_NAME, args.port, app)
    print u'Serving on http://{}:{}/'.format(HOST_NAME, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    sys.exit(main())
