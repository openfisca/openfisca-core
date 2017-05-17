# -*- coding: utf-8 -*-

import traceback
import warnings

import numpy as np

from formulas import ADD, DIVIDE


class Entity(object):
    key = None
    plural = None
    label = None
    is_person = False

    def __init__(self, simulation):
        self.simulation = simulation
        self.count = 0
        self.step_size = 0

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self, attribute)
        if not projector:
            raise Exception("Entity {} has no attribute {}".format(self.key, attribute))
        return projector

    @classmethod
    def to_json(cls):
        return {
            'isPersonsEntity': cls.is_person,
            'key': cls.key,
            'label': cls.label,
            'plural': cls.plural,
            'roles': cls.roles_description,
            }

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

    def check_role_validity(self, role):
        if role is not None and not type(role) == Role:
            raise Exception("{} is not a valid role".format(role))

    def check_period_validity(self, variable_name, period):
        if period is None:
            stack = traceback.extract_stack()
            filename, line_number, function_name, line_of_code = stack[-3]
            raise ValueError(u'''
You requested computation of variable "{}", but you did not specify on which period in "{}:{}":
    {}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <https://doc.openfisca.fr/coding-the-legislation/35_periods.html#periods-for-variable>.
'''.format(variable_name, filename, line_number, line_of_code).encode('utf-8'))

    def __call__(self, variable_name, period = None, options = [], **parameters):
        self.check_variable_defined_for_entity(variable_name)

        self.check_period_validity(variable_name, period)

        if ADD in options and DIVIDE in options:
            raise ValueError(u'Options ADD and DIVIDE are incompatible (trying to compute variable {})'.format(variable_name).encode('utf-8'))
        elif ADD in options:
            return self.simulation.calculate_add(variable_name, period, **parameters)
        elif DIVIDE in options:
            return self.simulation.calculate_divide(variable_name, period, **parameters)
        else:
            return self.simulation.calculate(variable_name, period, **parameters)

    # Helpers

    def empty_array(self):
        return np.zeros(self.count)

    def filled_array(self, value, dtype = None):
        with warnings.catch_warnings():  # Avoid a non-relevant warning
            warnings.simplefilter("ignore")
            return np.full(self.count, value, dtype)


class PersonEntity(Entity):
    is_person = True

    # Projection person -> person

    def has_role(self, role):
        self.check_role_validity(role)
        entity = self.simulation.get_entity(role.entity_class)
        if role.subroles:
            return np.logical_or.reduce([entity.members_role == subrole for subrole in role.subroles])
        else:
            return entity.members_role == role

    def value_from_partner(self, array, entity, role):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)

        if not role.subroles or not len(role.subroles) == 2:
            raise Exception('Projection to partner is only implemented for roles having exactly two subroles.')

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.project(entity.value_from_person(array, subrole_1))
        value_subrole_2 = entity.project(entity.value_from_person(array, subrole_2))

        return np.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
            )


class GroupEntity(Entity):
    roles = None
    flattened_roles = None
    roles_description = None

    def __init__(self, simulation):
        Entity.__init__(self, simulation)
        self.members_entity_id = None
        self._members_role = None
        self._members_position = None
        self.members_legacy_role = None
        self.members = self.simulation.persons

    @property
    def members_role(self):
        if self._members_role is None and self.members_legacy_role is not None:
            self._members_role = np.asarray([
                self.flattened_roles[legacy_role] if legacy_role < len(self.flattened_roles) else self.flattened_roles[-1]
                for legacy_role in self.members_legacy_role
                ])
        return self._members_role

    @property
    def members_position(self):
        if self._members_position is None and self.members_entity_id is not None:
            # We could use self.count and self.members.count , but with the current initilization, we are not sure count will be set before members_position is called
            nb_entities = np.max(self.members_entity_id) + 1
            nb_persons = len(self.members_entity_id)
            self._members_position = np.empty_like(self.members_entity_id)
            counter_by_entity = np.zeros(nb_entities)
            for k in range(nb_persons):
                entity_index = self.members_entity_id[k]
                self._members_position[k] = counter_by_entity[entity_index]
                counter_by_entity[entity_index] += 1

        return self._members_position

    @members_role.setter
    def members_role(self, members_role):
        self._members_role = members_role

    #  Aggregation persons -> entity

    def sum(self, array, role = None):
        self.check_role_validity(role)
        self.simulation.persons.check_array_compatible_with_entity(array)
        if role is not None:
            role_filter = self.members.has_role(role)
            return np.bincount(
                self.members_entity_id[role_filter],
                weights = array[role_filter],
                minlength = self.count)
        else:
            return np.bincount(self.members_entity_id, weights = array)

    def any(self, array, role = None):
        sum_in_entity = self.sum(array, role = role)
        return (sum_in_entity > 0)

    def reduce(self, array, reducer, neutral_element, role = None):
        self.simulation.persons.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True

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
        return self.reduce(array, reducer = np.logical_and, neutral_element = True, role = role)

    def max(self, array, role = None):
        return self.reduce(array, reducer = np.maximum, neutral_element = - np.infty, role = role)

    def min(self, array, role = None):
        return self.reduce(array, reducer = np.minimum, neutral_element = np.infty, role = role)

    def nb_persons(self, role = None):
        if role:
            role_condition = self.members.has_role(role)
            return self.sum(role_condition)
        else:
            return np.bincount(self.members_entity_id)

    # Projection person -> entity

    def value_from_person(self, array, role, default = 0):
        self.check_role_validity(role)
        if role.max != 1:
            raise Exception(
                'You can only use value_from_person with a role that is unique in {}. Role {} is not unique.'
                .format(self.key, role.key)
                )
        self.simulation.persons.check_array_compatible_with_entity(array)
        result = self.filled_array(default, dtype = array.dtype)
        role_filter = self.members.has_role(role)
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
        self.check_role_validity(role)
        role_condition = self.members.has_role(role) if role is not None else True
        return np.where(role_condition, array[self.members_entity_id], 0)

    # Does it really make sense ? Should not we use roles instead of position when projecting on someone in particular ?
    # Doesn't seem to be used, maybe should just not introduce
    def project_on_first_person(self, array):
        self.check_array_compatible_with_entity(array)
        entity_position_array = self.members_position
        entity_index_array = self.members_entity_id
        position_filter = (entity_position_array == 0)
        return np.where(position_filter, array[entity_index_array], 0)

    def share_between_members(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        nb_persons_per_entity = self.nb_persons(role)
        return self.project(array / nb_persons_per_entity, role = role)

    # Projection entity -> entity

    # Doesn't seem to be used either, as we can do entity1.first_person.entity2
    # Maybe should not introduce
    def transpose(self, array, origin_entity):
        origin_entity = self.simulation.get_entity(origin_entity)
        origin_entity.check_array_compatible_with_entity(array)
        input_projected = origin_entity.project(array)
        return self.value_from_first_person(input_projected)


class Role(object):

    def __init__(self, description, entity):
        self.entity_class = entity
        self.key = description['key']
        self.label = description.get('label')
        self.plural = description.get('plural')
        self.max = description.get('max')
        self.subroles = None


class Projector(object):
    reference_entity = None
    parent = None

    def __getattr__(self, attribute):
        return (get_projector_from_shortcut(self.reference_entity, attribute, parent = self) or getattr(self.reference_entity, attribute))

    def __call__(self, *args, **kwargs):
        result = self.reference_entity(*args, **kwargs)
        return self.transform_and_bubble_up(result)

    def transform_and_bubble_up(self, result):
        transformed_result = self.transform(result)
        if self.parent is None:
            return transformed_result
        else:
            return self.parent.transform_and_bubble_up(transformed_result)

    def transform(self, result):
        return NotImplementedError()


# For instance person.family
class EntityToPersonProjector(Projector):

    def __init__(self, entity, parent = None):
        self.reference_entity = entity
        self.parent = parent

    def transform(self, result):
        return self.reference_entity.project(result)


# For instance famille.first_person
class FirstPersonToEntityProjector(Projector):

    def __init__(self, entity, parent = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent

    def transform(self, result):
        return self.target_entity.value_from_first_person(result)


# For instance famille.declarant_principal
class UniqueRoleToEntityProjector(Projector):

    def __init__(self, entity, role, parent = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.target_entity.value_from_person(result, self.role)


def build_entity(key, plural, label, roles = None, is_person = False):
    entity_class_name = key.title()
    attributes = {'key': key, 'plural': plural, 'label': label, 'roles_description': roles}
    if is_person:
        entity_class = type(entity_class_name, (PersonEntity,), attributes)
    elif roles:
        entity_class = type(entity_class_name, (GroupEntity,), attributes)
        entity_class.roles = []
        for role_description in roles:
            role = Role(role_description, entity_class)
            entity_class.roles.append(role)
            setattr(entity_class, role.key.upper(), role)
            if role_description.get('subroles'):
                role.subroles = []
                for subrole_key in role_description['subroles']:
                    subrole = Role({'key': subrole_key, 'max': 1}, entity_class)
                    setattr(entity_class, subrole.key.upper(), subrole)
                    role.subroles.append(subrole)
                role.max = len(role.subroles)
        entity_class.flattened_roles = sum([role2.subroles or [role2] for role2 in entity_class.roles], [])

    return entity_class


def get_projector_from_shortcut(entity, shortcut, parent = None):
    if entity.is_person:
        if shortcut in entity.simulation.entities:
            entity_2 = entity.simulation.entities[shortcut]
            return EntityToPersonProjector(entity_2, parent)
    else:
        if shortcut == 'first_person':
            return FirstPersonToEntityProjector(entity, parent)
        role = next((role for role in entity.flattened_roles if (role.max == 1) and (role.key == shortcut)), None)
        if role:
            return UniqueRoleToEntityProjector(entity, role, parent)
