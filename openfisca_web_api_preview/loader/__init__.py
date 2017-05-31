# -*- coding: utf-8 -*-

import os

import yaml

from .tax_benefit_system import build_tax_benefit_system
from .parameters import build_parameters
from .variables import build_variables

OPEN_API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, 'openAPI.yml')


def extract_description(items):
    return {
        name: {'description': item['description']}
        for name, item in items.iteritems()
        }


def build_openAPI_specification(country_package_metadata):
    file = open(OPEN_API_CONFIG_FILE, 'r')
    spec = yaml.load(file)
    country_package_name = country_package_metadata['name'].title()
    spec['info']['title'] = spec['info']['title'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name)
    spec['info']['description'] = spec['info']['description'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name)
    spec['host'] = os.environ.get('SERVER_NAME')
    return spec


def build_data(country_package_name):
    tax_benefit_system = build_tax_benefit_system(country_package_name)
    country_package_metadata = tax_benefit_system.get_package_metadata()
    parameters = build_parameters(tax_benefit_system)
    variables = build_variables(tax_benefit_system, country_package_metadata)
    openAPI_spec = build_openAPI_specification(country_package_metadata)
    return {
        'tax_benefit_system': tax_benefit_system,
        'country_package_metadata': tax_benefit_system.get_package_metadata(),
        'openAPI_spec': openAPI_spec,
        'parameters': parameters,
        'parameters_description': extract_description(parameters),
        'variables': variables,
        'variables_description': extract_description(variables),
        }
