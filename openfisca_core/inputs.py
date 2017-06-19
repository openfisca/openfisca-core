# -*- coding: utf-8 -*-

from jsonschema import validate, ValidationError
import dpath

from taxbenefitsystems import VariableNotFound


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


def get_entities_schema(entity, tax_benefit_system):
    return {
        'type': 'object',
        'additionalProperties': get_entity_schema(entity, tax_benefit_system)
    }


def get_situation_schema(tax_benefit_system):
    return {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            entity.plural: get_entities_schema(entity, tax_benefit_system)
            for entity in tax_benefit_system.entities
        }
    }

def build_simulation(situation, tax_benefit_system):
    json_schema = get_situation_schema(tax_benefit_system)
    try:
        validate(situation, json_schema)
    except ValidationError as e:

        if len(e.path) == 0 and e.validator == "type":
            raise SituationParsingError(['error'],
                'Invalid type: a situation must be of type "object".')

        if len(e.path) == 0 and e.validator == "additionalProperties":
            unknown_entity = e.message.split("'")[1]
            e.path.append(unknown_entity)
            raise SituationParsingError(e.path,
                'This entity is not defined in the loaded tax and benefit system.')

        if len(e.path) == 2 and e.validator == "additionalProperties":
            unknown_variable_name = e.message.split("'")[1]
            e.path.append(unknown_variable_name)
            unknown_variable = tax_benefit_system.get_column(unknown_variable_name)
            if unknown_variable:
                declared_entity = e.path[-2]
                right_entity = unknown_variable.entity.plural
                raise SituationParsingError(e.path,
                u'You tried to set the value of variable {0} for {1}.'
                + u'but {0} is only defined for {2}'.format(unknown_variable_name, declared_entity, right_entity)
                )
            else:
                raise SituationParsingError(e.path,
                    VariableNotFound.build_error_message(unknown_variable_name, tax_benefit_system))


        raise SituationParsingError(e.path, e.message)



class SituationParsingError(Exception):
    def __init__(self, path, message):
        self.error = {}
        dpath_path = '/'.join([node for node in path if isinstance(node, basestring)])
        dpath.util.new(self.error, dpath_path, message)
