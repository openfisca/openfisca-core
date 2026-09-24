from __future__ import annotations

import typing

import numpy

from openfisca_core import entities, indexed_enums, projectors

from . import types as t
from .population import Population


def positions(members_entity_id):
    # We could use self.count and self.members.count , but with the current initialization, we are not sure count will be set before members_position is called
    nb_entities = numpy.max(members_entity_id) + 1
    nb_members = len(members_entity_id)
    # Sort persons by entity to group them
    order = numpy.argsort(members_entity_id, kind="stable")
    sorted_ids = members_entity_id[order]
    # Compute the start index of each entity's group in the sorted array
    group_sizes = numpy.bincount(sorted_ids, minlength=nb_entities)
    group_starts = numpy.empty(nb_entities, dtype=numpy.intp)
    group_starts[0] = 0
    numpy.cumsum(group_sizes[:-1], out=group_starts[1:])
    # Position within group = global sorted index - group start
    positions_sorted = numpy.arange(nb_members) - group_starts[sorted_ids]
    # Scatter back to original order
    members_position = numpy.empty(nb_members, dtype=numpy.int32)
    members_position[order] = positions_sorted
    return members_position


class Membership:
    def __init__(
        self, relationship, population: Population, members: t.Members
    ) -> None:
        self.population = population
        self.members = members
        self.relationship = relationship
        self._members_entity_id = None
        self._members_role = None
        self._members_position = None
        self._ordered_members_map = None

    def clone(self, relationship, population, members):
        result = Membership(relationship, population, members)
        result._members_entity_id = self._members_entity_id
        result._members_role = self._members_role
        result._members_position = self._members_position
        result._ordered_members_map = self._ordered_members_map
        return result

    @property
    def members_position(self):
        if self._members_position is None and self.members_entity_id is not None:
            self._members_position = positions(self.members_entity_id)
        return self._members_position

    @members_position.setter
    def members_position(self, members_position) -> None:
        self._members_position = members_position

    @property
    def members_entity_id(self):
        return self._members_entity_id

    @members_entity_id.setter
    def members_entity_id(self, members_entity_id) -> None:
        self._members_entity_id = members_entity_id

    @property
    def members_role(self):
        if self._members_role is None:
            default_role = self.relationship.a.flattened_roles[0]
            self._members_role = numpy.repeat(default_role, len(self.members_entity_id))
        return self._members_role

    @members_role.setter
    def members_role(self, members_role: typing.Iterable[entities.Role]) -> None:
        if members_role is not None:
            self._members_role = numpy.array(list(members_role))

    @property
    def ordered_members_map(self):
        """Mask to group the persons by entity
        This function only caches the map value, to see what the map is used for, see value_nth_person method.
        """
        if self._ordered_members_map is None:
            self._ordered_members_map = numpy.argsort(self.members_entity_id)
        return self._ordered_members_map

    # Helpers

    def get_role(self, role_name):
        return next(
            (role for role in self.relationship.a.flattened_roles if role.key == role_name),
            None,
        )

    #  Aggregation persons -> entity

    @projectors.projectable
    def sum(self, array, role=None):
        """Return the sum of ``array`` for the members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.sum(salaries)
        >>> array([3500])

        """
        self.relationship.a.check_role_validity(role)
        self.members.check_array_compatible_with_entity(array)
        if role is not None:
            role_filter = self.members.has_role(role)
            return numpy.bincount(
                self.members_entity_id[role_filter],
                weights=array[role_filter],
                minlength=self.population.count,
            )
        return numpy.bincount(self.members_entity_id, weights=array)

    @projectors.projectable
    def any(self, array, role=None):
        """Return ``True`` if ``array`` is ``True`` for any members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.any(salaries >= 1800)
        >>> array([True])

        """
        sum_in_entity = self.sum(array, role=role)
        return sum_in_entity > 0

    @projectors.projectable
    def reduce(self, array, reducer, neutral_element, role=None):
        self.members.check_array_compatible_with_entity(array)
        self.relationship.a.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True
        filtered_array = numpy.where(role_filter, array, neutral_element)

        result = self.population.filled_array(
            neutral_element,
        )  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentially slow if there are a lot of entities
        biggest_entity_size = numpy.max(position_in_entity) + 1

        for p in range(biggest_entity_size):
            values = self.value_nth_person(p, filtered_array, default=neutral_element)
            result = reducer(result, values)

        return result

    @projectors.projectable
    def all(self, array, role=None):
        """Return ``True`` if ``array`` is ``True`` for all members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.all(salaries >= 1800)
        >>> array([False])

        """
        return self.reduce(
            array,
            reducer=numpy.logical_and,
            neutral_element=True,
            role=role,
        )

    @projectors.projectable
    def max(self, array, role=None):
        """Return the maximum value of ``array`` for the entity members.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.max(salaries)
        >>> array([2000])

        """
        return self.reduce(
            array,
            reducer=numpy.maximum,
            neutral_element=-numpy.inf,
            role=role,
        )

    @projectors.projectable
    def min(self, array, role=None):
        """Return the minimum value of ``array`` for the entity members.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.min(salaries)
        >>> array([0])
        >>> household.min(
        ...     salaries, role=Household.PARENT
        ... )  # Assuming the 1st two persons are parents
        >>> array([1500])

        """
        return self.reduce(
            array,
            reducer=numpy.minimum,
            neutral_element=numpy.inf,
            role=role,
        )

    @projectors.projectable
    def nb_members(self, role=None):
        """Returns the number of persons contained in the entity.

        If ``role`` is provided, only the entity member with the given role are taken into account.
        """
        if role:
            if role.subroles:
                role_condition = numpy.logical_or.reduce(
                    [self.members_role == subrole for subrole in role.subroles],
                )
            else:
                role_condition = self.members_role == role
            return self.sum(role_condition)
        return numpy.bincount(self.members_entity_id)

    # Projection person -> entity
    @projectors.projectable
    def value_from_person(self, array, role, default=0):
        """Get the value of ``array`` for the person with the unique role ``role``.

        ``array`` must have the dimension of the number of persons in the simulation

        If such a person does not exist, return ``default`` instead

        The result is a vector which dimension is the number of entities
        """
        self.relationship.a.check_role_validity(role)
        if role.max != 1:
            msg = f"You can only use value_from_person with a role that is unique in {self.key}. Role {role.key} is not unique."
            raise Exception(
                msg,
            )
        self.members.check_array_compatible_with_entity(array)
        members_map = self.ordered_members_map
        result = self.population.filled_array(default, dtype=array.dtype)
        if isinstance(array, indexed_enums.EnumArray):
            result = indexed_enums.EnumArray(result, array.possible_values)
        role_filter = self.members.has_role(role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[members_map][role_filter[members_map]]

        return result

    @projectors.projectable
    def value_nth_person(self, n, array, default=0):
        """Get the value of array for the person whose position in the entity is n.

        Note that this position is arbitrary, and that members are not sorted.

        If the nth person does not exist, return  ``default`` instead.

        The result is a vector which dimension is the number of entities.
        """
        self.members.check_array_compatible_with_entity(array)
        positions = self.members_position
        nb_members_per_entity = self.nb_members()
        members_map = self.ordered_members_map
        result = self.population.filled_array(default, dtype=array.dtype)
        # For households that have at least n persons, set the result as the value of criteria for the person for which the position is n.
        # The map is needed b/c the order of the nth persons of each household in the persons vector is not necessarily the same than the household order.
        result[nb_members_per_entity > n] = array[members_map][
            positions[members_map] == n
        ]

        if isinstance(array, indexed_enums.EnumArray):
            result = indexed_enums.EnumArray(result, array.possible_values)

        return result

    @projectors.projectable
    def value_from_first_person(self, array):
        return self.value_nth_person(0, array)

    # Projection entity -> person(s)

    def project(self, array, role=None):
        self.population.check_array_compatible_with_entity(array)
        self.relationship.a.check_role_validity(role)
        if role is None:
            return array[self.members_entity_id]
        role_condition = self.members.has_role(role)
        return numpy.where(role_condition, array[self.members_entity_id], 0)

    @projectors.projectable
    def value_from_partner(
        self,
        array: t.FloatArray,
        entity: projectors.Projector,
        role: t.Role,
    ) -> None | t.FloatArray:
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)

        if not role.subroles or len(role.subroles) != 2:
            msg = "Projection to partner is only implemented for roles having exactly two subroles."
            raise Exception(
                msg,
            )

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.value_from_person(array, subrole_1)
        value_subrole_2 = entity.value_from_person(array, subrole_2)

        return numpy.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
        )
    
    @projectors.projectable
    def get_rank(
        self,
        population: Population,
        criteria: t.FloatArray,
        condition: bool = True,
    ) -> t.IntArray:
        """Get the rank of a person within an population according to a criteria.
        The person with rank 0 has the minimum value of criteria.
        If condition is specified, then the persons who don't respect it are not taken into account and their rank is -1.

        Example:
        >>> age = person("age", period)  # e.g [32, 34, 2, 8, 1]
        >>> person.get_rank(household, age)
        >>> [3, 4, 0, 2, 1]

        >>> is_child = person.has_role(
        ...     Household.CHILD
        ... )  # [False, False, True, True, True]
        >>> person.get_rank(
        ...     household, -age, condition=is_child
        ... )  # Sort in reverse order so that the eldest child gets the rank 0.
        >>> [-1, -1, 1, 0, 2]

        """
        # If population is for instance 'person.household', we get the reference population 'household' behind the projector
        population = (
            population
            if not isinstance(population, projectors.Projector)
            else population.reference_entity
        )

        positions = self.members_position
        biggest_entity_size = numpy.max(positions) + 1
        filtered_criteria = numpy.where(condition, criteria, numpy.inf)
        ids = self.members_entity_id

        # Matrix: the value in line i and column j is the value of criteria for the jth person of the ith entity
        matrix = numpy.asarray(
            [
                population.value_nth_person(k, filtered_criteria, default=numpy.inf)
                for k in range(biggest_entity_size)
            ],
        ).transpose()

        # We double-argsort all lines of the matrix.
        # Double-argsorting gets the rank of each value once sorted
        # For instance, if x = [3,1,6,4,0], y =  numpy.argsort(x) is [4, 1, 0, 3, 2] (because the value with index 4 is the smallest one, the value with index 1 the second smallest, etc.) and z =  numpy.argsort(y) is [2, 1, 4, 3, 0], the rank of each value.
        sorted_matrix = numpy.argsort(numpy.argsort(matrix))

        # Build the result vector by taking for each person the value in the right line (corresponding to its household id) and the right column (corresponding to its position)
        result = sorted_matrix[ids, positions]

        # Return -1 for the persons who don't respect the condition
        return numpy.where(condition, result, -1)
