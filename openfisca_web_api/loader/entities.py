# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from openfisca_core.commons import to_unicode


def build_entities(tax_benefit_system):
    entities = {
        entity.key: build_entity(entity)
        for entity in tax_benefit_system.entities
        }
    return entities


def build_entity(entity):

    entity_formated = {
        'plural': entity.plural,
        'description': to_unicode(entity.doc)
        }
    if hasattr(entity, 'roles'):
        entity_formated['roles'] = \
            {
            role.key: build_role(role)
            for role in entity.roles
            }
    return entity_formated


def build_role(role):
    role_formated = {
        'plural': role.plural,
        'description': role.doc
        }

    if role.max:
        role_formated['max'] = role.max
    if role.subroles:
        role_formated['max'] = len(role.subroles)

    role_formated['mandatory'] = True if role_formated.get('max') else False
    return role_formated
