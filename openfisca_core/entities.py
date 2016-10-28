# -*- coding: utf-8 -*-

import numpy as np
import warnings

from enumerations import Enum
from formulas import ADD, DIVIDE


class Entity(object):
    key = None
    plural = None
    label = None
    roles = None
    is_person = False

    def __init__(self, simulation):
        self.simulation = simulation
        self.count = 0
        self.step_size = 0

    # Calculations

    def check_variable_defined_for_entity(self, variable_name):
        if not (self.simulation.get_variable_entity(variable_name) == self):
            variable_entity = self.simulation.get_variable_entity(variable_name)
            raise Exception(
                "Variable {} is not defined for {} but for {}".format(
                    variable_name, self.key, variable_entity.key)
                )

    def check_array_compatible_with_entity(self, array):
        if not self.count == array.size:
            raise Exception("Input {} is not a valid value for the entity {}".format(array, self.key))

    def __call__(self, variable_name, period = None, options = []):
        self.check_variable_defined_for_entity(variable_name)

        if ADD in options and DIVIDE in options:
            return self.simulation.calculate_add_divide(variable_name, period)
        elif ADD in options:
            return self.simulation.calculate_add(variable_name, period)
        elif DIVIDE in options:
            return self.simulation.calculate_divide(variable_name, period)
        else:
            return self.simulation.calculate(variable_name, period)

    # Helpers

    def empty_array(self):
        return np.zeros(self.count)

    def filled_array(self, value):
        with warnings.catch_warnings():  # Avoid a non-relevant warning
            warnings.simplefilter("ignore")
            return np.full(self.count, value)


class PersonEntity(Entity):
    is_person = True

    # Projection person -> person

    def has_role(self, role, entity):  # if a role was not just a number, we could have only role as arg.
        entity = self.simulation.get_entity(entity)
        return entity.members_role == role

    def value_from_partner(self, array, entity, role):
        # Make sure there is only two people with the role
        self.check_array_compatible_with_entity(array)
        entity_filter = entity.nb_persons(role) == 2
        higher_value = entity_filter * entity.max(array, role)
        lower_value = entity_filter * entity.min(array, role)
        higher_value_i = entity.project(higher_value, role)
        lower_value_i = entity.project(lower_value, role)
        return (array == higher_value_i) * lower_value_i + (array == lower_value_i) * higher_value_i


class GroupEntity(Entity):

    @classmethod
    def get_role_enum(cls):
        return Enum(map(lambda role: role['key'], cls.roles))

    def __init__(self, simulation):
        Entity.__init__(self, simulation)
        self.members_entity_id = None
        self.members_role = None
        self.members_legacy_role = None
        self.members_position = None
        self.first_person = FirstPersonToEntityProjector(self)
        self.members = self.simulation.persons

    #  Aggregation persons -> entity

    def sum(self, array, role = None):
        self.simulation.persons.check_array_compatible_with_entity(array)
        result = self.empty_array()
        if role is not None:
            role_filter = (self.members_role == role)

            # Entities for which one person at least has the given role
            entity_has_role_filter = np.bincount(self.members_entity_id, weights = role_filter) > 0

            result[entity_has_role_filter] += np.bincount(self.members_entity_id[role_filter], weights = array[role_filter])
        else:
            result += np.bincount(self.members_entity_id, weights = array)
        return result

    def any(self, array, role = None):
        sum_in_entity = self.sum(array, role = role)
        return (sum_in_entity > 0)

    def reduce(self, array, reducer, neutral_element, role = None):
        self.simulation.persons.check_array_compatible_with_entity(array)
        position_in_entity = self.members_position
        role_in_entity = self.members_role
        role_filter = (role_in_entity == role) if role is not None else True

        result = self.filled_array(neutral_element)  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentielly slow if there are a lot of entities
        nb_positions = np.max(position_in_entity) + 1
        for p in range(nb_positions):
            filter = (position_in_entity == p) * role_filter
            entity_filter = self.any(filter)
            result[entity_filter] = reducer(result[entity_filter], array[filter])

        return result

    def all(self, array, role = None):
        return self.reduce(array, neutral_element = True, reducer = np.logical_and, role = role)

    def max(self, array, role = None):
        return self.reduce(array, neutral_element = - np.infty, reducer = np.maximum, role = role)

    def min(self, array, role = None):
        return self.reduce(array, neutral_element = np.infty, reducer = np.minimum, role = role)

    def nb_persons(self, role = None):
            role_condition = (self.members_role == role)
            return self.sum(role_condition)

    # Projection person -> entity

    def value_from_person(self, array, role, default = 0):
        # TODO: Make sure the role is unique
        self.simulation.persons.check_array_compatible_with_entity(array)
        result = self.filled_array(default)
        role_filter = (self.members_role == role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[role_filter]

        return result

    def value_from_first_person(self, array):
        self.simulation.persons.check_array_compatible_with_entity(array)
        position_filter = (self.members_position == 0)

        return array[position_filter]

    # Projection entity -> person(s)

    def project(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        role_condition = (self.members_role == role) if role is not None else True
        return array[self.members_entity_id] * role_condition

    def project_on_first_person(self, array):
        self.check_array_compatible_with_entity(array)
        entity_position_array = self.members_position
        entity_index_array = self.members_entity_id
        boolean_filter = (entity_position_array == 0)
        return array[entity_index_array] * boolean_filter

    def share_between_members(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        nb_persons_per_entity = self.nb_persons(role)
        return self.project(array / nb_persons_per_entity, role = role)

    # Projection entity -> entity

    def transpose(self, array, origin_entity):
        origin_entity = self.simulation.get_entity(origin_entity)
        origin_entity.check_array_compatible_with_entity(array)
        input_projected = origin_entity.project_on_first_person(array)
        return self.sum(input_projected)  # TODO: What if it is a string ?


class EntityToPersonProjector(object):

    def __init__(self, entity):
        self.entity = entity

    def __getattr__(self, attribute):
        return getattr(self.entity, attribute)

    def __call__(self, *args, **kwargs):
        result = self.entity(*args, **kwargs)
        return self.entity.project(result)


class FirstPersonToEntityProjector(object):

    def __init__(self, entity):
        self.entity = entity

    def __getattr__(self, attribute):
        # seulement les entities de group
        if attribute in self.entity.simulation.entities.keys():
            origin_entity = self.simulation.entities[attribute]
            return EntityToEntityProjector(origin_entity, self.entity)

        return getattr(self.entity.members, attribute)

    def __call__(self, *args, **kwargs):
        result = self.entity.members(*args, **kwargs)
        return self.entity.value_from_first_person(result)


class EntityToEntityProjector(object):

    def __init__(self, origin_entity, target_entity):
        self.origin_entity = origin_entity
        self.target_entity = target_entity

    def __getattr__(self, attribute):
        return getattr(self.origin_entity.members, attribute)

    def __call__(self, *args, **kwargs):
        result = self.origin_entity(*args, **kwargs)
        return self.target_entity.transpose(result, origin_entity = self.origin_entity)
