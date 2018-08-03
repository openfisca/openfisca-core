# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from copy import deepcopy

from openfisca_core.columns import make_column_from_variable
from openfisca_core import conv
from openfisca_core.commons import basestring_type


def check_entity_fields(entity_json, entity_class, valid_roles, tax_benefit_system):

    def check_id(value):
        if value is None or not isinstance(value, (basestring_type, int)):
            raise ValueError("Invalid id in entity {}".format(entity_json).encode('utf-8'))

    def check_role(value, key):
        role = valid_roles.get(key)
        if role.max == 1:
            value, error = conv.test_isinstance((basestring_type, int))(value)
        else:
            value, error = conv.pipe(
                conv.make_item_to_singleton(),
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.test_isinstance((basestring_type, int)),
                    drop_none_items = True,
                    )
                )(value)

        if error is not None:
            raise ValueError("Invalid description of {}: {}. Error: {}".format(entity_class.key, entity_json, error).encode('utf-8'))
        entity_json[key] = value

    def check_variable(value, key):
        variable = tax_benefit_system.variables[key]
        column = make_column_from_variable(variable)
        if column.entity != entity_class:
            raise ValueError("Variable {} is defined for entity {}. It cannot be set for entity {}.".format(key, column.entity.key, entity_class.key).encode('utf-8'))
        value, error = column.json_to_python(value)
        if error is not None:
            raise ValueError("Invalid value {} for variable {}. Error: {}".format(value, key, error).encode('utf-8'))
        entity_json[key] = value

    for key, value in entity_json.items():
        if key == 'id':
            check_id(value)
        elif valid_roles.get(key) is not None:
            check_role(value, key)
        elif tax_benefit_system.variables.get(key) is not None:
            check_variable(value, key)
        else:
            # We only import VariableNotFound here to avoid a circular dependency in imports
            from .taxbenefitsystems import VariableNotFound
            raise VariableNotFound(key, tax_benefit_system)

    for role in valid_roles.values():
        if role.max != 1 and entity_json.get(role.plural) is None:  # by convention, if no one in the entity has a given non-unique role, it should be [] in the JSON
            entity_json[role.plural] = []


def check_entities_and_role(test_case, tax_benefit_system, state):
    """
        Check that the test_case describes entities consistent with the tax and benefit system.

        Will raise an error if :
            - An entity is not recognized
            - An entity role is not recognized
            - A variable is declared for an entity it is not defined for (e.g. salary for a family)
    """

    test_case = deepcopy(test_case)  # Avoid side-effects on other references to test_case
    entity_classes = {entity_class.plural: entity_class for entity_class in tax_benefit_system.entities}
    for entity_type_name, entities in test_case.items():
        if entity_classes.get(entity_type_name) is None:
            raise ValueError("Invalid entity name: {}".format(entity_type_name).encode('utf-8'))
        entities, error = conv.pipe(
            conv.make_item_to_singleton(),
            conv.test_isinstance(list),
            conv.uniform_sequence(
                conv.test_isinstance(dict),
                drop_none_items = True,
                ),
            conv.function(set_entities_json_id),
            )(entities)
        if error is not None:
            raise ValueError("Invalid list of {}: {}. Error: {}".format(entity_type_name, entities, error).encode('utf-8'))
        if entities is None:
            entities = test_case[entity_type_name] = []  # YAML test runner may set these values to None
        entity_class = entity_classes[entity_type_name]
        valid_roles = dict(
            (role.key, role) if (role.max == 1) else (role.plural, role)
            for role in entity_class.roles
            ) if not entity_class.is_person else {}

        for entity_json in entities:
            check_entity_fields(entity_json, entity_class, valid_roles, tax_benefit_system)

    for entity_class in entity_classes.values():
        if test_case.get(entity_class.plural) is None:
            test_case[entity_class.plural] = []  # by convention, all entities must be declared in the test_case

    return test_case


def check_entities_consistency(test_case, tax_benefit_system, state):
    """
        Checks that every person belongs to at most one entity of each kind
    """

    remaining_persons = {
        entity.plural: [person['id'] for person in test_case[tax_benefit_system.person_entity.plural]]
        for entity in tax_benefit_system.group_entities
        }

    def build_role_checker(role, entity):
        if role.max == 1:
            return role.key, conv.test_in_pop(remaining_persons[entity.plural])
        else:
            return role.plural, conv.uniform_sequence(conv.test_in_pop(remaining_persons[entity.plural]))

    entity_parsing_dict = {
        entity.plural: conv.uniform_sequence(
            conv.struct(
                dict(
                    build_role_checker(role, entity)
                    for role in entity.roles
                    ),
                default = conv.noop,
                ),
            )
        for entity in tax_benefit_system.group_entities
        }

    test_case, error = conv.struct(
        entity_parsing_dict,
        default = conv.noop,
        )(test_case, state = state)

    return test_case, error, remaining_persons


def check_each_person_has_entities(test_case, tax_benefit_system, state):
    groupless_persons = check_entities_consistency(test_case, tax_benefit_system, state)[2]
    groupless_persons_ids = sum(groupless_persons.values(), [])  # all the persons who are missing an entity
    error = None
    if groupless_persons_ids:
        individu_index_by_id = {
            individu['id']: individu_index
            for individu_index, individu in enumerate(test_case[tax_benefit_system.person_entity.plural])
            }
        error = {}
        for person_id in groupless_persons_ids:
            error.setdefault(tax_benefit_system.person_entity.plural, {})[individu_index_by_id[person_id]] = state._(
                "Individual is missing from {}").format(
                    state._(' & ').join(
                        word
                        for word in [
                            entity.plural if person_id in groupless_persons[entity.plural] else None
                            for entity in tax_benefit_system.group_entities
                            ]
                        if word is not None
                        ))
    return test_case, error


def set_entities_json_id(entities_json):
    for index, entity_json in enumerate(entities_json):
        if 'id' not in entity_json:
            entity_json['id'] = index
    return entities_json
