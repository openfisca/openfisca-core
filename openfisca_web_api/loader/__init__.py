# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

from openfisca_web_api.loader.parameters import build_parameters
from openfisca_web_api.loader.variables import build_variables
from openfisca_web_api.loader.entities import build_entities
from openfisca_web_api.loader.spec import build_openAPI_specification


def build_data(tax_benefit_system):
    country_package_metadata = tax_benefit_system.get_package_metadata()
    parameters = build_parameters(tax_benefit_system, country_package_metadata)
    variables = build_variables(tax_benefit_system, country_package_metadata)
    data = {
        'tax_benefit_system': tax_benefit_system,
        'country_package_metadata': tax_benefit_system.get_package_metadata(),
        'openAPI_spec': None,
        'parameters': parameters,
        'variables': variables,
        'entities': build_entities(tax_benefit_system),
        }
    data['openAPI_spec'] = build_openAPI_specification(data)

    return data
