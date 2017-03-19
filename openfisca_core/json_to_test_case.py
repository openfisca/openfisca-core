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
                # conv.uniform_sequence(
                #     conv.struct(
                #         dict(itertools.chain(
                #             dict(
                #                 id = conv.pipe(
                #                     conv.test_isinstance((basestring, int)),
                #                     conv.not_none,
                #                     ),
                #                 ).iteritems(),
                #             get_role_parsing_dict(entity).iteritems(),
                #             (
                #                 (column.name, column.json_to_python)
                #                 for column in column_by_name.itervalues()
                #                 if column.entity == entity
                #                 ),
                #             )),
                #         drop_none_values = True,
                #         ),
                #     drop_none_items = True,
                #     ),
                conv.default([]),
                )
            for entity in tax_benefit_system.entities
            }



    test_case, error = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(get_entity_parsing_dict(tax_benefit_system)),
        )(test_case, state = state)

    entity_classes = { entity_class.plural: entity_class for entity_class in tax_benefit_system.entities }
    for entity_type_name, entities in test_case.iteritems():
        if entity_type_name not in entity_classes.keys():
            raise ValueError(u"Invalid entity name: {}".format(entity_type_name))
        entity_class = entity_classes[entity_type_name]
        valid_roles = [role.key if role.max == 1 else role.plural for role in entity_class.roles] if not entity_class.is_person else []
        for entity in entities:
            for key, value in entity.iteritems():
                if key == 'id':
                    if value is None or not isinstance(value, (basestring, int)):
                        raise ValueError(u"Invalid id in entity {}".format(entity))
                elif key in valid_roles:
                    value, error = conv.pipe(
                        conv.make_item_to_singleton(),
                        conv.test_isinstance(list),
                        conv.uniform_sequence(
                            conv.test_isinstance((basestring, int)),
                            drop_none_items = True,
                            )
                        )(value)
                    if error is not None:
                        raise ValueError(u"Invalid description of {}: {}. Error: {}".format(entity_class.key, entity, error))
                    entity[key] = value
                elif tax_benefit_system.column_by_name.get(key) is not None:
                    column = tax_benefit_system.column_by_name[key]
                    if column.entity != entity_class:
                        raise ValueError(u"Variable {} is defined for entity {}. It cannot be set for entity {}.".format(key, column.entity.key, entity_class.key))
                    value, error = column.json_to_python(value)
                    if error is not None:
                        raise ValueError(u"Invalid value {} for variable {}. Error: {}".format(value, key, error))
                    entity[key] = value
                else:
                    from .taxbenefitsystems import VariableNotFound
                    raise VariableNotFound(u"Variable {} doesn't exist in this tax and benefit system.".format(key))

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
