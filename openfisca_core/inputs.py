# -*- coding: utf-8 -*-

from jsonschema import validate, ValidationError
import dpath

def get_entity_schema(entity, tax_benefit_system):
    if entity.is_person:
        return {
            'type': 'object',
            'properties': {
                variable_name : {'type': 'object'}
                for variable_name in tax_benefit_system.get_variables(entity)
                },
            'additionalProperties': False,
            }
    else:
        properties = {}
        properties.update({
            role.plural: {
                'type': 'array',
                "items": {
                    "type": "string"
                    }
                }
            for role in entity.roles
            })
        properties.update({
            variable_name : {'type': 'object'}
            for variable_name in tax_benefit_system.get_variables(entity)
            })
        return {
            'type': 'object',
            'properties': properties,
            'additionalProperties': False,
            }

def get_schema(tax_benefit_system):
    return {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            entity.plural: get_entity_schema(entity, tax_benefit_system)
            for entity in tax_benefit_system.entities
        }
    }

def build_simulation(situation, tax_benefit_system):
    json_schema = get_schema(tax_benefit_system)
    try:
        validate(situation, json_schema)
    except ValidationError as e:
        if len(e.path) == 0 and e.validator == "type":
            if not isinstance(situation, dict):
                raise SituationParsingError({
                    'error': 'Invalid type: a situation must be of type "object".'
                    })
        if len(e.path) == 0 and e.validator == "additionalProperties":
            raise SituationParsingError({
                e.message.split("'")[1]: 'This entity is not defined in the loaded tax and benefit system.'
                })

        if len(e.path) == 1 and e.validator == "additionalProperties":
            raise SituationParsingError({
                e.message.split("'")[1]: 'This entity is not defined in the loaded tax and benefit system.'
                })


        response = {}
        dpath.util.new(response, '/'.join([node for node in e.path if isinstance(node, str)]), e.message)
        raise SituationParsingError(response)



class SituationParsingError(Exception):
    def __init__(self, error):
        self.error = error
