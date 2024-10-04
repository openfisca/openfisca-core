from typing import NoReturn

import logging

log = logging.getLogger("gunicorn.error")


def handle_import_error(error) -> NoReturn:
    msg = f"OpenFisca is missing some dependencies to run the Web API: '{error}'. To install them, run `pip install openfisca_core[web-api]`."
    raise ImportError(
        msg,
    )
