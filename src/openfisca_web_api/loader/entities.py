# -*- coding: utf-8 -*-


def build_entities(tax_benefit_system):
    entities = {
        entity.key: build_entity(entity)
        for entity in tax_benefit_system.entities
        }
    return entities


def build_entity(entity):
    formatted_doc = entity.doc.strip()

    formatted_entity = {
        'plural': entity.plural,
        'description': entity.label,
        'documentation': formatted_doc
        }
    if not entity.is_person:
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

    return formatted_role
