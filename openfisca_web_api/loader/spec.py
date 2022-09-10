import os
from copy import deepcopy

import dpath
import yaml

from openfisca_core.indexed_enums import Enum
from openfisca_web_api import handlers

OPEN_API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, 'openAPI.yml')


def build_openAPI_specification(api_data):
    tax_benefit_system = api_data['tax_benefit_system']

    with open(OPEN_API_CONFIG_FILE, encoding = "utf-8") as file:
        spec = yaml.safe_load(file)

    country_package_name = api_data['country_package_metadata']['name'].title()
    dpath.util.new(spec, 'info/title', spec['info']['title'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name))
    dpath.util.new(spec, 'info/description', spec['info']['description'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name))
    dpath.util.new(spec, 'info/version', api_data['country_package_metadata']['version'])

    for entity in tax_benefit_system.entities:
        name = entity.key.title()
        spec['definitions'][name] = get_entity_json_schema(entity, tax_benefit_system)

    situation_schema = get_situation_json_schema(tax_benefit_system)
    dpath.util.new(spec, 'definitions/SituationInput', situation_schema)
    dpath.util.new(spec, 'definitions/SituationOutput', situation_schema.copy())
    dpath.util.new(spec, 'definitions/Trace/properties/entitiesDescription/properties', {
        entity.plural: {'type': 'array', 'items': {"type": "string"}}
        for entity in tax_benefit_system.entities
        })

    # Get example from the served tax benefist system

    if tax_benefit_system.open_api_config.get('parameter_example'):
        parameter_id = tax_benefit_system.open_api_config['parameter_example']
        parameter_path = parameter_id.replace('.', '/')
        parameter_example = api_data['parameters'][parameter_path]
    else:
        parameter_example = next(iter(api_data['parameters'].values()))
    dpath.util.new(spec, 'definitions/Parameter/example', parameter_example)

    if tax_benefit_system.open_api_config.get('variable_example'):
        variable_example = api_data['variables'][tax_benefit_system.open_api_config['variable_example']]
    else:
        variable_example = next(iter(api_data['variables'].values()))
    dpath.util.new(spec, 'definitions/Variable/example', variable_example)

    if tax_benefit_system.open_api_config.get('simulation_example'):
        simulation_example = tax_benefit_system.open_api_config['simulation_example']
        dpath.util.new(spec, 'definitions/SituationInput/example', simulation_example)
        dpath.util.new(spec, 'definitions/SituationOutput/example', handlers.calculate(tax_benefit_system, deepcopy(simulation_example)))  # calculate has side-effects
        dpath.util.new(spec, 'definitions/Trace/example', handlers.trace(tax_benefit_system, simulation_example))
    else:
        message = f"No simulation example has been defined for this tax and benefit system. If you are the maintainer of {country_package_name}, you can define an example by following this documentation: https://openfisca.org/doc/openfisca-web-api/config-openapi.html"
        dpath.new(spec, 'definitions/SituationInput/example', message)
        dpath.new(spec, 'definitions/SituationOutput/example', message)
        dpath.new(spec, 'definitions/Trace/example', message)
    return spec


def get_variable_json_schema(variable):
    result = {
        'type': 'object',
        'additionalProperties': {'type': variable.json_type},
        }

    if variable.value_type == Enum:
        result['additionalProperties']['enum'] = [item.name for item in list(variable.possible_values)]

    return result


def get_entity_json_schema(entity, tax_benefit_system):
    if entity.is_person:
        return {
            'type': 'object',
            'properties': {
                variable_name: get_variable_json_schema(variable)
                for variable_name, variable in tax_benefit_system.get_variables(entity).items()
                },
            'additionalProperties': False,
            }

    properties = {}
    properties.update({
        role.plural or role.key: {
            'type': 'array',
            "items": {
                "type": "string"
                }
            }
        for role in entity.roles
        })
    properties.update({
        variable_name: get_variable_json_schema(variable)
        for variable_name, variable in tax_benefit_system.get_variables(entity).items()
        })
    return {
        'type': 'object',
        'properties': properties,
        'additionalProperties': False,
        }


def get_situation_json_schema(tax_benefit_system):
    return {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            entity.plural: {
                'type': 'object',
                'additionalProperties': {
                    "$ref": f"#/definitions/{entity.key.title()}"
                    }
                }
            for entity in tax_benefit_system.entities
            }
        }
