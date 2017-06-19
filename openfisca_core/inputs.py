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


def check_type(input, type, path):
    type_map = {
        dict: "object",
        list: "array",
        str: "string"
    }

    if not isinstance(input, type):
        raise SituationParsingError(path,
            'Invalid type: must be of type "{}".'.format(type_map[type]))


def check_entity(entity_object, entity_class, roles_by_plural, tax_benefit_system, path):
    check_type(entity_object, dict, path)

    for property_name, property in entity_object.iteritems():
        if property_name in roles_by_plural:
            check_type(property, list, path + [property_name])
        else:
            check_variable(property_name, property, entity_class, tax_benefit_system, path + [property_name])


def check_variable(property_name, property, entity_class, tax_benefit_system, path):
    variable = tax_benefit_system.get_column(property_name)
    if not variable:
        raise SituationParsingError(path,
        VariableNotFound.build_error_message(property_name, tax_benefit_system),
        code = 404
        )
    if not variable.entity == entity_class:
        declared_entity = entity_class.plural
        right_entity = variable.entity.plural
        raise SituationParsingError(path,
            u'You tried to set the value of variable {0} for {1}, but {0} is only defined for {2}.'.format(property_name, declared_entity, right_entity)
        )
    else:
        if not isinstance(property, dict):
            raise SituationParsingError(path,
            'Input variables need to be set for a specific period. For instance: "{salary: {"2017-06": 2000}}"')


def build_simulation(situation, tax_benefit_system):
    check_type(situation, dict, ['error'])
    entities_by_plural = {
        entity.plural: entity
        for entity in tax_benefit_system.entities
    }

    for entity_plural, entities in situation.iteritems():
        entity_class = entities_by_plural.get(entity_plural)
        if not entity_class:
            raise SituationParsingError([entity_plural],
                'This entity is not defined in the loaded tax and benefit system.')
        check_type(entities, dict, [entity_plural])

        roles_by_plural = {
            role.plural: role
            for role in entity_class.roles
        } if not entity_class.is_person else {}

        for entity_id, entity_object in entities.iteritems():
            check_entity(entity_object, entity_class, roles_by_plural, tax_benefit_system, [entity_plural, entity_id])


class SituationParsingError(Exception):
    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join(path)
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
