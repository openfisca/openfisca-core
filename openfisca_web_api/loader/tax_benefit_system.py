import traceback
import logging

from openfisca_core import commons

log = logging.getLogger(__name__)


def build_tax_benefit_system(country_package_name):
    try:
        country_package = commons.import_country_package(country_package_name)

    except ImportError as error:
        raise ValueError(str(error)) from error

    try:
        return country_package.CountryTaxBenefitSystem()

    except NameError:  # Gunicorn swallows NameErrors. Force printing the stack trace.
        log.error(traceback.format_exc())
        raise
