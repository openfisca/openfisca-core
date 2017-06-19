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

def build_simulation_old(situation, tax_benefit_system):
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
                    VariableNotFound.build_error_message(unknown_variable_name, tax_benefit_system),
                    code = 404
                    )


        raise SituationParsingError(e.path, e.message)


def build_simulation(situation, tax_benefit_system):
    if not isinstance(situation, dict):
        raise SituationParsingError(['error'],
                'Invalid type: a situation must be of type "object".')

    entities_by_plural = {
        entity.plural: entity
        for entity in tax_benefit_system.entities
    }

    for entity_plural, entities in situation.iteritems():
        entity_class = entities_by_plural.get(entity_plural)
        if not entity_class:
            raise SituationParsingError([entity_plural],
                'This entity is not defined in the loaded tax and benefit system.')
        if not isinstance(entities, dict):
           raise SituationParsingError([entity_plural],
                'Invalid type: must be of type "object".')

        roles_by_plural = {
            role.plural: role
            for role in entity_class.roles
        } if not entity_class.is_person else {}

        for entity_id, entity_object in entities.iteritems():
            if not isinstance(entity_object, dict):
              raise SituationParsingError([entity_plural, entity_id],
                'Invalid type: must be of type "object".')

            for property_name, property in entity_object.iteritems():
                if property_name in roles_by_plural:
                    if not isinstance(property, list):
                        raise SituationParsingError([entity_plural, entity_id, property_name],
                'Invalid type: must be of type "array".')
                elif property_name in tax_benefit_system.column_by_name:
                    variable = tax_benefit_system.get_column(property_name)
                    if not variable.entity == entity_class:
                        declared_entity = entity_class.plural
                        right_entity = variable.entity.plural
                        raise SituationParsingError([entity_plural, entity_id, property_name],
                            u'You tried to set the value of variable {0} for {1}, but {0} is only defined for {2}.'.format(property_name, declared_entity, right_entity)
                        )
                    else:
                        if not isinstance(property, dict):
                            raise SituationParsingError([entity_plural, entity_id, property_name],
                    'Input variables need to be set for a specific period. For instance: "{salary: {"2017-06": 2000}}"')
                else:
                    raise SituationParsingError([entity_plural, entity_id, property_name],
                    VariableNotFound.build_error_message(property_name, tax_benefit_system),
                    code = 404
                    )





class SituationParsingError(Exception):
    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join([node for node in path if isinstance(node, basestring)])
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
