# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

def build_entities(tax_benefit_system):
    entities = {
        entity.key: {
            "plural": entity.plural,
            "description": entity.doc
        }
        for entity in tax_benefit_system.entities
    }
    return entities


