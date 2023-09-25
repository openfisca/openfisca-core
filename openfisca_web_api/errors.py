# -*- coding: utf-8 -*-

import logging

log = logging.getLogger("gunicorn.error")


def handle_import_error(error):
    raise ImportError(
        "OpenFisca is missing some dependencies to run the Web API: '{}'. To install them, run `pip install openfisca_core[web-api]`.".format(
            error
        )
    )
