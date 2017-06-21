# -*- coding: utf-8 -*-

from tax_benefit_system import build_tax_benefit_system
from parameters import build_parameters
from variables import build_variables
from spec import build_openAPI_specification


def extract_description(items):
    return {
        name: {'description': item['description']}
        for name, item in items.iteritems()
        }


def build_data(country_package_name):
    tax_benefit_system = build_tax_benefit_system(country_package_name)
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
