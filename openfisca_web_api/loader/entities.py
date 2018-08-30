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

    formatted_entity = {
        'plural': entity.plural,
        'description': to_unicode(entity.label),
        'documentation': to_unicode(entity.doc)
        }
    if hasattr(entity, 'roles'):
        formatted_entity['roles'] = {
            role.key: build_role(role)
            for role in entity.roles
            }
    return formatted_entity


def build_role(role):
    formatted_role = {
        'plural': role.plural,
        'description': role.doc
        }

    if role.max:
        formatted_role['max'] = role.max
    if role.subroles:
        formatted_role['max'] = len(role.subroles)

    formatted_role['mandatory'] = True if formatted_role.get('max') else False
    return formatted_role
