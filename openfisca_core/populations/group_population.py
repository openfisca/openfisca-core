from __future__ import annotations

import typing

import numpy

from openfisca_core import entities, indexed_enums, projectors

from . import types as t
from .population import Population


class GroupPopulation(Population):
    def __init__(self, entity: t.GroupEntity, members: t.Members) -> None:
        super().__init__(entity)
        self.members = members
        self._members_entity_id = None
        self._members_role = None
        self._members_position = None
        self._ordered_members_map = None

    def clone(self, simulation):
        result = GroupPopulation(self.entity, self.members)
        result.simulation = simulation
        result._holders = {
            variable: holder.clone(self) for (variable, holder) in self._holders.items()
        }
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
            # We could use self.count and self.members.count , but with the current initialization, we are not sure count will be set before members_position is called
            nb_entities = numpy.max(self.members_entity_id) + 1
            nb_persons = len(self.members_entity_id)
            # Sort persons by entity to group them
            order = numpy.argsort(self.members_entity_id, kind="stable")
            sorted_ids = self.members_entity_id[order]
            # Compute the start index of each entity's group in the sorted array
            group_sizes = numpy.bincount(sorted_ids, minlength=nb_entities)
            group_starts = numpy.empty(nb_entities, dtype=numpy.intp)
            group_starts[0] = 0
            numpy.cumsum(group_sizes[:-1], out=group_starts[1:])
            # Position within group = global sorted index - group start
            positions_sorted = numpy.arange(nb_persons) - group_starts[sorted_ids]
            # Scatter back to original order
            self._members_position = numpy.empty(nb_persons, dtype=numpy.int32)
            self._members_position[order] = positions_sorted

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

    def set_members_entity_id(self, members_entity_id) -> None:
        """Set group structure from a person-indexed array of group entity ids.

        Updates ``members_entity_id`` and ``count`` (number of distinct groups),
        and clears internal caches so rank, value_nth_person, etc. use the new
        structure. Use this instead of assigning to ``members_entity_id`` and
        clearing private cache attributes manually.

        Args:
            members_entity_id: 1D array of length ``members.count``; value at
                index i is the group entity id for person i. Group ids must be
                0-based contiguous (0 .. K-1 for K groups).
        """
        arr = numpy.asarray(members_entity_id, dtype=numpy.int32)
        self._members_entity_id = arr
        self.count = int(numpy.max(arr)) + 1
        self._members_position = None
        self._ordered_members_map = None

    @property
    def members_role(self):
        if self._members_role is None:
            default_role = self.entity.flattened_roles[0]
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
            (role for role in self.entity.flattened_roles if role.key == role_name),
            None,
        )

    #  Filtering helpers

    def _build_member_mask(self, role=None, condition=None):
        """Build a combined boolean mask from role and condition filters.

        Returns None if no filtering is needed (both are None), otherwise
        returns a boolean array of length ``members.count``.
        """
        if role is None and condition is None:
            return None

        mask = numpy.ones(self.members.count, dtype=bool)

        if role is not None:
            role_filter = self.members.has_role(role)
            mask &= role_filter

        if condition is not None:
            mask &= condition

        return mask

    #  Aggregation persons -> entity

    @projectors.projectable
    def sum(self, array, role=None, condition=None):
        """Return the sum of ``array`` for the members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        taken into account.  ``role`` and ``condition`` can be combined.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.sum(salaries)
        >>> array([3500])

        """
        self.entity.check_role_validity(role)
        self.members.check_array_compatible_with_entity(array)
        mask = self._build_member_mask(role, condition)
        if mask is not None:
            return numpy.bincount(
                self.members_entity_id[mask],
                weights=array[mask],
                minlength=self.count,
            )
        return numpy.bincount(self.members_entity_id, weights=array)

    @projectors.projectable
    def any(self, array, role=None, condition=None):
        """Return ``True`` if ``array`` is ``True`` for any members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        taken into account.  ``role`` and ``condition`` can be combined.

        Example:
        >>> salaries = household.members(
        ...     "salary", "2018-01"
        ... )  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.any(salaries >= 1800)
        >>> array([True])

        """
        sum_in_entity = self.sum(array, role=role, condition=condition)
        return sum_in_entity > 0

    @projectors.projectable
    def reduce(self, array, reducer, neutral_element, role=None, condition=None):
        self.members.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        position_in_entity = self.members_position
        mask = self._build_member_mask(role, condition)
        if mask is None:
            mask = True  # scalar True broadcasts; preserves old upcast behavior
        filtered_array = numpy.where(mask, array, neutral_element)

        result = self.filled_array(
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
    def all(self, array, role=None, condition=None):
        """Return ``True`` if ``array`` is ``True`` for all members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        taken into account.  ``role`` and ``condition`` can be combined.

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
            condition=condition,
        )

    @projectors.projectable
    def max(self, array, role=None, condition=None):
        """Return the maximum value of ``array`` for the entity members.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        taken into account.  ``role`` and ``condition`` can be combined.

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
            condition=condition,
        )

    @projectors.projectable
    def min(self, array, role=None, condition=None):
        """Return the minimum value of ``array`` for the entity members.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        taken into account.  ``role`` and ``condition`` can be combined.

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
            condition=condition,
        )

    @projectors.projectable
    def nb_persons(self, role=None, condition=None):
        """Returns the number of persons contained in the entity.

        If ``role`` is provided, only the entity member with the given role are taken into account.

        If ``condition`` is provided (a boolean array of the same size as the
        person population), only members for whom the condition is ``True`` are
        counted.  ``role`` and ``condition`` can be combined.
        """
        if role:
            if role.subroles:
                role_condition = numpy.logical_or.reduce(
                    [self.members_role == subrole for subrole in role.subroles],
                )
            else:
                role_condition = self.members_role == role
            return self.sum(role_condition, condition=condition)
        if condition is not None:
            return self.sum(condition.astype(float)).astype(int)
        return numpy.bincount(self.members_entity_id)

    # Projection person -> entity

    @projectors.projectable
    def value_from_person(self, array, role, default=0):
        """Get the value of ``array`` for the person with the unique role ``role``.

        ``array`` must have the dimension of the number of persons in the simulation

        If such a person does not exist, return ``default`` instead

        The result is a vector which dimension is the number of entities
        """
        self.entity.check_role_validity(role)
        if role.max != 1:
            msg = f"You can only use value_from_person with a role that is unique in {self.key}. Role {role.key} is not unique."
            raise Exception(
                msg,
            )
        self.members.check_array_compatible_with_entity(array)
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype=array.dtype)
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
        nb_persons_per_entity = self.nb_persons()
        members_map = self.ordered_members_map
        nb_entities = len(nb_persons_per_entity)
        if nb_entities != self.count:
            raise ValueError(
                f"Group population '{self.entity.key}' is inconsistent: "
                f"count is {self.count} but members_entity_id implies "
                f"{nb_entities} entities (from bincount). "
                "Ensure count matches the number of entities implied by members_entity_id."
            )
        result = self.filled_array(default, dtype=array.dtype)
        # For households that have at least n persons, set the result as the value of criteria for the person for which the position is n.
        # The map is needed b/c the order of the nth persons of each household in the persons vector is not necessarily the same than the household order.
        result[nb_persons_per_entity > n] = array[members_map][
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
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        if role is None:
            return array[self.members_entity_id]
        role_condition = self.members.has_role(role)
        return numpy.where(role_condition, array[self.members_entity_id], 0)
