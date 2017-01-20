# -*- coding: utf-8 -*-

import itertools

from . import conv


def check_entities_and_role(test_case, tax_benefit_system, state):
    """
        Check that the test_case describes entities consistent with the tax and benefit system.

        Will raise an error if :
            - An entity is not recognized
            - An entity role is not recognized
            - A variable is declared for an entity it is not defined for (e.g. salary for a family)
    """

    def build_role_parser(role):
        if role.max == 1:
            return role.key, conv.test_isinstance((basestring, int))
        else:
            return role.plural, conv.pipe(
                conv.make_item_to_singleton(),
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.test_isinstance((basestring, int)),
                    drop_none_items = True,
                    ),
                conv.default([]),
                )

    def get_role_parsing_dict(entity):
        if entity.is_person:
            return {}
        else:
            return dict(
                build_role_parser(role)
                for role in entity.roles
                )

    def get_entity_parsing_dict(tax_benefit_system):
        column_by_name = tax_benefit_system.column_by_name
        return {
            entity.plural: conv.pipe(
                conv.make_item_to_singleton(),
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.test_isinstance(dict),
                    drop_none_items = True,
                    ),
                conv.function(set_entities_json_id),
                conv.uniform_sequence(
                    conv.struct(
                        dict(itertools.chain(
                            dict(
                                id = conv.pipe(
                                    conv.test_isinstance((basestring, int)),
                                    conv.not_none,
                                    ),
                                ).iteritems(),
                            get_role_parsing_dict(entity).iteritems(),
                            (
                                (column.name, column.json_to_python)
                                for column in column_by_name.itervalues()
                                if column.entity == entity
                                ),
                            )),
                        drop_none_values = True,
                        ),
                    drop_none_items = True,
                    ),
                conv.default([]),
                )
            for entity in tax_benefit_system.entities
            }

    test_case, error = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(get_entity_parsing_dict(tax_benefit_system)),
        )(test_case, state = state)

    return test_case, error


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
            individu[u'id']: individu_index
            for individu_index, individu in enumerate(test_case[tax_benefit_system.person_entity.plural])
            }
        error = {}
        for person_id in groupless_persons_ids:
            error.setdefault(tax_benefit_system.person_entity.plural, {})[individu_index_by_id[person_id]] = state._(
                u"Individual is missing from {}").format(
                    state._(u' & ').join(
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
