# -*- coding: utf-8 -*-

import traceback

from typing import Iterable

import numpy as np

from openfisca_core.entities import Role
from openfisca_core.indexed_enums import EnumArray
from openfisca_core.holders import Holder


ADD = 'add'
DIVIDE = 'divide'


def projectable(function):
    """
    Decorator to indicate that when called on a projector, the outcome of the function must be projected.
    For instance person.household.sum(...) must be projected on person, while it would not make sense for person.household.get_holder.
    """
    function.projectable = True
    return function


class Population(object):
    def __init__(self, entity):
        self.simulation = None
        self.entity = entity
        self._holders = {}
        self.count = 0
        self.ids = []

    def clone(self, simulation):
        result = Population(self.entity)
        result.simulation = simulation
        result._holders = {variable: holder.clone(result) for (variable, holder) in self._holders.items()}
        result.count = self.count
        result.ids = self.ids
        return result

    def empty_array(self):
        return np.zeros(self.count)

    def filled_array(self, value, dtype = None):
        return np.full(self.count, value, dtype)

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self, attribute)
        if not projector:
            raise AttributeError("You tried to use the '{}' of '{}' but that is not a known attribute.".format(attribute, self.entity.key))
        return projector

    def get_index(self, id):
        return self.ids.index(id)

    # Calculations

    def check_array_compatible_with_entity(self, array):
        if not self.count == array.size:
            raise ValueError("Input {} is not a valid value for the entity {} (size = {} != {} = count)".format(
                array, self.key, array.size, self.count))

    def check_period_validity(self, variable_name, period):
        if period is None:
            stack = traceback.extract_stack()
            filename, line_number, function_name, line_of_code = stack[-3]
            raise ValueError('''
You requested computation of variable "{}", but you did not specify on which period in "{}:{}":
    {}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-variable-definition>.
'''.format(variable_name, filename, line_number, line_of_code))

    def __call__(self, variable_name, period = None, options = None, **parameters):
        """
            Calculate the variable ``variable_name`` for the entity and the period ``period``, using the variable formula if it exists.

            Example:

            >>> person('salary', '2017-04')
            >>> array([300.])

            :returns: A numpy array containing the result of the calculation
        """
        self.entity.check_variable_defined_for_entity(variable_name)
        self.check_period_validity(variable_name, period)

        if options is None:
            options = []

        if ADD in options and DIVIDE in options:
            raise ValueError('Options ADD and DIVIDE are incompatible (trying to compute variable {})'.format(variable_name).encode('utf-8'))
        elif ADD in options:
            return self.simulation.calculate_add(variable_name, period, **parameters)
        elif DIVIDE in options:
            return self.simulation.calculate_divide(variable_name, period, **parameters)
        else:
            return self.simulation.calculate(variable_name, period, **parameters)

    # Helpers

    def get_holder(self, variable_name):
        self.entity.check_variable_defined_for_entity(variable_name)
        holder = self._holders.get(variable_name)
        if holder:
            return holder
        variable = self.entity.get_variable(variable_name)
        self._holders[variable_name] = holder = Holder(variable, self)
        return holder

    def get_memory_usage(self, variables = None):
        holders_memory_usage = {
            variable_name: holder.get_memory_usage()
            for variable_name, holder in self._holders.items()
            if variables is None or variable_name in variables
            }

        total_memory_usage = sum(
            holder_memory_usage['total_nb_bytes'] for holder_memory_usage in holders_memory_usage.values()
            )

        return dict(
            total_nb_bytes = total_memory_usage,
            by_variable = holders_memory_usage
            )

    @projectable
    def has_role(self, role):
        """
            Check if a person has a given role within its :any:`GroupEntity`

            Example:

            >>> person.has_role(Household.CHILD)
            >>> array([False])
        """
        self.entity.check_role_validity(role)
        group_population = self.simulation.get_population(role.entity.plural)
        if role.subroles:
            return np.logical_or.reduce([group_population.members_role == subrole for subrole in role.subroles])
        else:
            return group_population.members_role == role

    @projectable
    def value_from_partner(self, array, entity, role):
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)

        if not role.subroles or not len(role.subroles) == 2:
            raise Exception('Projection to partner is only implemented for roles having exactly two subroles.')

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.value_from_person(array, subrole_1)
        value_subrole_2 = entity.value_from_person(array, subrole_2)

        return np.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
            )

    @projectable
    def get_rank(self, entity, criteria, condition = True):
        """
        Get the rank of a person within an entity according to a criteria.
        The person with rank 0 has the minimum value of criteria.
        If condition is specified, then the persons who don't respect it are not taken into account and their rank is -1.

        Example:

        >>> age = person('age', period)  # e.g [32, 34, 2, 8, 1]
        >>> person.get_rank(household, age)
        >>> [3, 4, 0, 2, 1]

        >>> is_child = person.has_role(Household.CHILD)  # [False, False, True, True, True]
        >>> person.get_rank(household, - age, condition = is_child)  # Sort in reverse order so that the eldest child gets the rank 0.
        >>> [-1, -1, 1, 0, 2]
        """

        # If entity is for instance 'person.household', we get the reference entity 'household' behind the projector
        entity = entity if not isinstance(entity, Projector) else entity.reference_entity

        positions = entity.members_position
        biggest_entity_size = np.max(positions) + 1
        filtered_criteria = np.where(condition, criteria, np.inf)
        ids = entity.members_entity_id

        # Matrix: the value in line i and column j is the value of criteria for the jth person of the ith entity
        matrix = np.asarray([
            entity.value_nth_person(k, filtered_criteria, default = np.inf)
            for k in range(biggest_entity_size)
            ]).transpose()

        # We double-argsort all lines of the matrix.
        # Double-argsorting gets the rank of each value once sorted
        # For instance, if x = [3,1,6,4,0], y = np.argsort(x) is [4, 1, 0, 3, 2] (because the value with index 4 is the smallest one, the value with index 1 the second smallest, etc.) and z = np.argsort(y) is [2, 1, 4, 3, 0], the rank of each value.
        sorted_matrix = np.argsort(np.argsort(matrix))

        # Build the result vector by taking for each person the value in the right line (corresponding to its household id) and the right column (corresponding to its position)
        result = sorted_matrix[ids, positions]

        # Return -1 for the persons who don't respect the condition
        return np.where(condition, result, -1)


class GroupPopulation(Population):
    def __init__(self, entity, members):
        super().__init__(entity)
        self.members = members
        self._members_entity_id = None
        self._members_role = None
        self._members_position = None
        self._ordered_members_map = None

    def clone(self, simulation):
        result = GroupPopulation(self.entity, self.members)
        result.simulation = simulation
        result._holders = {variable: holder.clone(self) for (variable, holder) in self._holders.items()}
        result.count = self.count
        result.ids = self.ids
        result._members_entity_id = self._members_entity_id
        result._members_role = self._members_role
        result._members_position = self._members_position
        result._ordered_members_map = self._ordered_members_map
        return result

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

    @property
    def members_entity_id(self):
        return self._members_entity_id

    @members_entity_id.setter
    def members_entity_id(self, members_entity_id):
        self._members_entity_id = members_entity_id

    @property
    def members_role(self):
        if self._members_role is None:
            default_role = self.entity.flattened_roles[0]
            self._members_role = np.repeat(default_role, len(self.members_entity_id))
        return self._members_role

    @members_role.setter
    def members_role(self, members_role: Iterable[Role]):
        if members_role is not None:
            self._members_role = np.array(list(members_role))

    @property
    def ordered_members_map(self):
        """
        Mask to group the persons by entity
        This function only caches the map value, to see what the map is used for, see value_nth_person method.
        """
        if self._ordered_members_map is None:
            return np.argsort(self.members_entity_id)
        return self._ordered_members_map

    def get_role(self, role_name):
        return next((role for role in self.entity.flattened_roles if role.key == role_name), None)

    @members_position.setter
    def members_position(self, members_position):
        self._members_position = members_position

    #  Aggregation persons -> entity

    @projectable
    def sum(self, array, role = None):
        """
            Return the sum of ``array`` for the members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.sum(salaries)
            >>> array([3500])
        """
        self.entity.check_role_validity(role)
        self.members.check_array_compatible_with_entity(array)
        if role is not None:
            role_filter = self.members.has_role(role)
            return np.bincount(
                self.members_entity_id[role_filter],
                weights = array[role_filter],
                minlength = self.count)
        else:
            return np.bincount(self.members_entity_id, weights = array)

    @projectable
    def any(self, array, role = None):
        """
            Return ``True`` if ``array`` is ``True`` for any members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.any(salaries >= 1800)
            >>> array([True])
        """
        sum_in_entity = self.sum(array, role = role)
        return (sum_in_entity > 0)

    @projectable
    def reduce(self, array, reducer, neutral_element, role = None):
        self.members.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True
        filtered_array = np.where(role_filter, array, neutral_element)

        result = self.filled_array(neutral_element)  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentielly slow if there are a lot of entities
        biggest_entity_size = np.max(position_in_entity) + 1

        for p in range(biggest_entity_size):
            values = self.value_nth_person(p, filtered_array, default = neutral_element)
            result = reducer(result, values)

        return result

    @projectable
    def all(self, array, role = None):
        """
            Return ``True`` if ``array`` is ``True`` for all members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.all(salaries >= 1800)
            >>> array([False])
        """
        return self.reduce(array, reducer = np.logical_and, neutral_element = True, role = role)

    @projectable
    def max(self, array, role = None):
        """
            Return the maximum value of ``array`` for the entity members.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.max(salaries)
            >>> array([2000])
        """
        return self.reduce(array, reducer = np.maximum, neutral_element = - np.infty, role = role)

    @projectable
    def min(self, array, role = None):
        """
            Return the minimum value of ``array`` for the entity members.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.min(salaries)
            >>> array([0])
            >>> household.min(salaries, role = Household.PARENT)  # Assuming the 1st two persons are parents
            >>> array([1500])
        """
        return self.reduce(array, reducer = np.minimum, neutral_element = np.infty, role = role)

    @projectable
    def nb_persons(self, role = None):
        """
            Returns the number of persons contained in the entity.

            If ``role`` is provided, only the entity member with the given role are taken into account.
        """
        if role:
            if role.subroles:
                role_condition = np.logical_or.reduce([self.members_role == subrole for subrole in role.subroles])
            else:
                role_condition = self.members_role == role
            return self.sum(role_condition)
        else:
            return np.bincount(self.members_entity_id)

    # Projection person -> entity

    @projectable
    def value_from_person(self, array, role, default = 0):
        """
            Get the value of ``array`` for the person with the unique role ``role``.

            ``array`` must have the dimension of the number of persons in the simulation

            If such a person does not exist, return ``default`` instead

            The result is a vector which dimension is the number of entities
        """
        self.entity.check_role_validity(role)
        if role.max != 1:
            raise Exception(
                'You can only use value_from_person with a role that is unique in {}. Role {} is not unique.'
                .format(self.key, role.key)
                )
        self.members.check_array_compatible_with_entity(array)
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype = array.dtype)
        if isinstance(array, EnumArray):
            result = EnumArray(result, array.possible_values)
        role_filter = self.members.has_role(role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[members_map][role_filter[members_map]]

        return result

    @projectable
    def value_nth_person(self, n, array, default = 0):
        """
            Get the value of array for the person whose position in the entity is n.

            Note that this position is arbitrary, and that members are not sorted.

            If the nth person does not exist, return  ``default`` instead.

            The result is a vector which dimension is the number of entities.
        """
        self.members.check_array_compatible_with_entity(array)
        positions = self.members_position
        nb_persons_per_entity = self.nb_persons()
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype = array.dtype)
        # For households that have at least n persons, set the result as the value of criteria for the person for which the position is n.
        # The map is needed b/c the order of the nth persons of each household in the persons vector is not necessarily the same than the household order.
        result[nb_persons_per_entity > n] = array[members_map][positions[members_map] == n]

        return result

    @projectable
    def value_from_first_person(self, array):
        return self.value_nth_person(0, array)

    # Projection entity -> person(s)

    def project(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        if role is None:
            return array[self.members_entity_id]
        else:
            role_condition = self.members.has_role(role)
            return np.where(role_condition, array[self.members_entity_id], 0)


class Projector(object):
    reference_entity = None
    parent = None

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self.reference_entity, attribute, parent = self)
        if projector:
            return projector

        reference_attr = getattr(self.reference_entity, attribute)
        if not hasattr(reference_attr, 'projectable'):
            return reference_attr

        def projector_function(*args, **kwargs):
            result = reference_attr(*args, **kwargs)
            return self.transform_and_bubble_up(result)

        return projector_function

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


def get_projector_from_shortcut(population, shortcut, parent = None):
    if population.entity.is_person:
        if shortcut in population.simulation.populations:
            entity_2 = population.simulation.populations[shortcut]
            return EntityToPersonProjector(entity_2, parent)
    else:
        if shortcut == 'first_person':
            return FirstPersonToEntityProjector(population, parent)
        role = next((role for role in population.entity.flattened_roles if (role.max == 1) and (role.key == shortcut)), None)
        if role:
            return UniqueRoleToEntityProjector(population, role, parent)
