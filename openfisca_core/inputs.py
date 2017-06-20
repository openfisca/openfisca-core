# -*- coding: utf-8 -*-


def get_entity_schema(entity, tax_benefit_system):
    if entity.is_person:
        return {
            'type': 'object',
            'properties': {
                variable_name: {'type': 'object'}
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
            variable_name: {'type': 'object'}
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
