# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

from openfisca_web_api.loader.parameters import build_parameters
from openfisca_web_api.loader.variables import build_variables
from openfisca_web_api.loader.spec import build_openAPI_specification


def build_data(tax_benefit_system):
    country_package_metadata = tax_benefit_system.get_package_metadata()
    parameters = build_parameters(tax_benefit_system, country_package_metadata)
    variables = build_variables(tax_benefit_system, country_package_metadata)
    openAPI_spec = build_openAPI_specification(tax_benefit_system, country_package_metadata)
    return {
        'tax_benefit_system': tax_benefit_system,
        'country_package_metadata': tax_benefit_system.get_package_metadata(),
        'openAPI_spec': openAPI_spec,
        'parameters': parameters,
        'variables': variables,
        'host': None  # Will be set by mirroring requests
        }
