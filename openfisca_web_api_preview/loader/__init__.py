# -*- coding: utf-8 -*-

from openfisca_web_api_preview.loader.parameters import build_parameters
from openfisca_web_api_preview.loader.variables import build_variables
from openfisca_web_api_preview.loader.spec import build_openAPI_specification


def extract_description(items):
    return {
        name: {'description': item['description']}
        for name, item in items.items()
        }


def build_data(tax_benefit_system):
    country_package_metadata = tax_benefit_system.get_package_metadata()
    parameters = build_parameters(tax_benefit_system)
    variables = build_variables(tax_benefit_system, country_package_metadata)
    openAPI_spec = build_openAPI_specification(tax_benefit_system, country_package_metadata)
    return {
        'tax_benefit_system': tax_benefit_system,
        'country_package_metadata': tax_benefit_system.get_package_metadata(),
        'openAPI_spec': openAPI_spec,
        'parameters': parameters,
        'parameters_description': extract_description(parameters),
        'variables': variables,
        'variables_description': extract_description(variables),
        }
