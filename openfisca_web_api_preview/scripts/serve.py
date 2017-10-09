# -*- coding: utf-8 -*-

import os
import sys
import argparse
from wsgiref.simple_server import make_server

from openfisca_core.scripts import add_tax_benefit_system_arguments, detect_country_package
from ..app import create_app
# from _tkinter import create
# from ..application import make_app

HOST_NAME = 'localhost'
BASE_CONF = {
    'debug': 'true',
    }

# old:
# paster serve --reload development-france.ini 

# COUNTRY_PACKAGE=openfisca_country_template 
# gunicorn "openfisca_web_api_preview.app:create_app()" 
# --bind localhost:5000 --workers 3
# TRACKER_URL
# TRACKER_IDSITE
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', action = 'store', default = 5000, help = "port to serve on", type = int)
    parser = add_tax_benefit_system_arguments(parser)
    args = parser.parse_args()

    tracker_url = os.environ.get('TRACKER_URL')
    tracker_idsite = os.environ.get('TRACKER_IDSITE')

    app = create_app(args.country_package, args.extensions, tracker_url, tracker_idsite)
    httpd = make_server(HOST_NAME, args.port, app)
    print u'Serving on http://{}:{}/'.format(HOST_NAME, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    sys.exit(main())
