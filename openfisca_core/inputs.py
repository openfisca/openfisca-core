# -*- coding: utf-8 -*-

from jsonschema import validate, ValidationError

json_schema = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'persons': {'type': 'object'}
    }
}

def build_simulation(situation, tax_benefit_system):
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



    #     if entity not in [loaded_entity.plural for loaded_entity in tax_benefit_system.entities]:
    #         raise SituationParsingError({
    #             entity: 'This entity is not defined in the loaded tax and benefit system.'
    #             })



class SituationParsingError(Exception):
    def __init__(self, error):
        self.error = error
