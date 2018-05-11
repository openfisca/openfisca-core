# -*- coding: utf-8 -*-

import os

import yaml

from openfisca_core.indexed_enums import Enum


OPEN_API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, 'openAPI.yml')


def build_openAPI_specification(tax_benefit_system, country_package_metadata):
    file = open(OPEN_API_CONFIG_FILE, 'r')
    spec = yaml.load(file)
    country_package_name = country_package_metadata['name'].title()
    spec['info']['title'] = spec['info']['title'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name)
    spec['info']['description'] = spec['info']['description'].replace("{COUNTRY_PACKAGE_NAME}", country_package_name)
    spec['host'] = os.environ.get('SERVER_NAME')

    for entity in tax_benefit_system.entities:
        name = entity.key.title()
        spec['definitions'][name] = get_entity_json_schema(entity, tax_benefit_system)

    situation_schema = get_situation_json_schema(tax_benefit_system)
    spec['definitions']['SituationInput'].update(situation_schema)
    spec['definitions']['SituationOutput'].update(situation_schema)
    spec['definitions']['Trace']['properties']['entitiesDescription']['properties'] = {
        entity.plural: {'type': 'array', 'items': {"type": "string"}}
        for entity in tax_benefit_system.entities
        }

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
    else:
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
                    "$ref": "#/definitions/{}".format(entity.key.title())
                    }
                }
            for entity in tax_benefit_system.entities
            }
        }
