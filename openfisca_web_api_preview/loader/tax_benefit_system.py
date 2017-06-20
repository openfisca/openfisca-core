# -*- coding: utf-8 -*-

import importlib
import traceback
from os import linesep


def build_tax_benefit_system(country_package_name):
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        message = linesep.join([traceback.format_exc(),
                                u'Could not import module `{}`.'.format(country_package_name).encode('utf-8'),
                                u'Are you sure it is installed in your environment? If so, look at the stack trace above to determine the origin of this error.',
                                u'See more at <https://github.com/openfisca/country-template#installing>.',
                                linesep])
        raise ValueError(message)
    return country_package.CountryTaxBenefitSystem()
