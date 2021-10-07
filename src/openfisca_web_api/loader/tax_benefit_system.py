# -*- coding: utf-8 -*-

import importlib
import traceback
import logging
from os import linesep

log = logging.getLogger(__name__)


def build_tax_benefit_system(country_package_name):
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        message = linesep.join([traceback.format_exc(),
                                'Could not import module `{}`.'.format(country_package_name),
                                'Are you sure it is installed in your environment? If so, look at the stack trace above to determine the origin of this error.',
                                'See more at <https://github.com/openfisca/country-template#installing>.',
                                linesep])
        raise ValueError(message)
    try:
        return country_package.CountryTaxBenefitSystem()
    except NameError:  # Gunicorn swallows NameErrors. Force printing the stack trace.
        log.error(traceback.format_exc())
        raise
