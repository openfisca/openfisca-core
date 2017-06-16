# -*- coding: utf-8 -*-

def build_simulation(situation, tax_benefit_system):
    if not isinstance(situation, dict):
        raise SituationParsingError({
            'error': 'Invalid type: a situation must be of type "object".'
            })

    for entity in situation.keys():
        if entity not in [loaded_entity.plural for loaded_entity in tax_benefit_system.entities]:
            raise SituationParsingError({
                entity: 'This entity is not defined in the loaded tax and benefit system.'
                })


class SituationParsingError(Exception):
    def __init__(self, error):
        self.error = error
