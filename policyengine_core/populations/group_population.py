from typing import Callable, Any, TYPE_CHECKING
import numpy
from numpy.typing import ArrayLike
from policyengine_core import projectors
from policyengine_core.entities import Role, Entity
from policyengine_core.enums import EnumArray
from policyengine_core.populations import Population

if TYPE_CHECKING:
    from policyengine_core.simulations import Simulation


class GroupPopulation(Population):
    def __init__(self, entity: Entity, members: Population):
        super().__init__(entity)
        self.members: Population = members
        self._members_entity_id: ArrayLike = None
        self._members_role: ArrayLike = None
        self._members_position: ArrayLike = None
        self._ordered_members_map = None

    def clone(self, simulation: "Simulation") -> "GroupPopulation":
        result = GroupPopulation(self.entity, self.members)
        result.simulation = simulation
        result._holders = {
            variable: holder.clone(self)
            for (variable, holder) in self._holders.items()
        }
        result.count = self.count
        result.ids = self.ids
        result._members_entity_id = self._members_entity_id
        result._members_role = self._members_role
        result._members_position = self._members_position
        result._ordered_members_map = self._ordered_members_map
        return result

    @property
    def members_position(self) -> ArrayLike:
        if (
            self._members_position is None
            and self.members_entity_id is not None
        ):
            # We could use self.count and self.members.count , but with the current initilization, we are not sure count will be set before members_position is called
            nb_entities = numpy.max(self.members_entity_id) + 1
            nb_persons = len(self.members_entity_id)
            self._members_position = numpy.empty_like(self.members_entity_id)
            counter_by_entity = numpy.zeros(nb_entities)
            for k in range(nb_persons):
                entity_index = self.members_entity_id[k]
                self._members_position[k] = counter_by_entity[entity_index]
                counter_by_entity[entity_index] += 1

        return self._members_position

    @members_position.setter
    def members_position(self, members_position: ArrayLike) -> None:
        self._members_position = members_position

    @property
    def members_entity_id(self) -> ArrayLike:
        return self._members_entity_id

    @members_entity_id.setter
    def members_entity_id(self, members_entity_id: ArrayLike) -> None:
        self._members_entity_id = members_entity_id

    @property
    def members_role(self) -> ArrayLike:
        if self._members_role is None:
            default_role = self.entity.flattened_roles[0]
            self._members_role = numpy.repeat(
                default_role, len(self.members_entity_id)
            )
        return self._members_role

    @members_role.setter
    def members_role(self, members_role: ArrayLike):
        if members_role is not None:
            self._members_role = numpy.array(list(members_role))

    @property
    def ordered_members_map(self) -> ArrayLike:
        """
        Mask to group the persons by entity
        This function only caches the map value, to see what the map is used for, see value_nth_person method.
        """
        if self._ordered_members_map is None:
            self._ordered_members_map = numpy.argsort(self.members_entity_id)
        return self._ordered_members_map

    def get_role(self, role_name: str) -> Role:
        return next(
            (
                role
                for role in self.entity.flattened_roles
                if role.key == role_name
            ),
            None,
        )

    #  Aggregation persons -> entity

    @projectors.projectable
    def sum(self, array: ArrayLike, role: Role = None) -> ArrayLike:
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
            return numpy.bincount(
                self.members_entity_id[role_filter],
                weights=array[role_filter],
                minlength=self.count,
            )
        else:
            return numpy.bincount(self.members_entity_id, weights=array)

    @projectors.projectable
    def any(self, array: ArrayLike, role: Role = None) -> ArrayLike:
        """
        Return ``True`` if ``array`` is ``True`` for any members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:

        >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.any(salaries >= 1800)
        >>> array([True])
        """
        sum_in_entity = self.sum(array, role=role)
        return sum_in_entity > 0

    @projectors.projectable
    def reduce(
        self,
        array: ArrayLike,
        reducer: Callable,
        neutral_element: Any,
        role: Role = None,
    ) -> ArrayLike:
        self.members.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True
        filtered_array = numpy.where(role_filter, array, neutral_element)

        result = self.filled_array(
            neutral_element
        )  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentielly slow if there are a lot of entities
        biggest_entity_size = numpy.max(position_in_entity) + 1

        for p in range(biggest_entity_size):
            values = self.value_nth_person(
                p, filtered_array, default=neutral_element
            )
            result = reducer(result, values)

        return result

    @projectors.projectable
    def all(self, array: ArrayLike, role: Role = None) -> ArrayLike:
        """
        Return ``True`` if ``array`` is ``True`` for all members of the entity.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:

        >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.all(salaries >= 1800)
        >>> array([False])
        """
        return self.reduce(
            array, reducer=numpy.logical_and, neutral_element=True, role=role
        )

    @projectors.projectable
    def max(self, array: ArrayLike, role: Role = None) -> ArrayLike:
        """
        Return the maximum value of ``array`` for the entity members.

        ``array`` must have the dimension of the number of persons in the simulation

        If ``role`` is provided, only the entity member with the given role are taken into account.

        Example:

        >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
        >>> household.max(salaries)
        >>> array([2000])
        """
        return self.reduce(
            array,
            reducer=numpy.maximum,
            neutral_element=-numpy.infty,
            role=role,
        )

    @projectors.projectable
    def min(self, array: ArrayLike, role: Role = None) -> ArrayLike:
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
        return self.reduce(
            array,
            reducer=numpy.minimum,
            neutral_element=numpy.infty,
            role=role,
        )

    @projectors.projectable
    def nb_persons(self, role: Role = None) -> ArrayLike:
        """
        Returns the number of persons contained in the entity.

        If ``role`` is provided, only the entity member with the given role are taken into account.
        """
        if role:
            if role.subroles:
                role_condition = numpy.logical_or.reduce(
                    [self.members_role == subrole for subrole in role.subroles]
                )
            else:
                role_condition = self.members_role == role
            return self.sum(role_condition)
        else:
            return numpy.bincount(self.members_entity_id)

    # Projection person -> entity

    @projectors.projectable
    def value_from_person(
        self, array: ArrayLike, role: Role, default: Any = 0
    ) -> ArrayLike:
        """
        Get the value of ``array`` for the person with the unique role ``role``.

        ``array`` must have the dimension of the number of persons in the simulation

        If such a person does not exist, return ``default`` instead

        The result is a vector which dimension is the number of entities
        """
        self.entity.check_role_validity(role)
        if role.max != 1:
            raise Exception(
                "You can only use value_from_person with a role that is unique in {}. Role {} is not unique.".format(
                    self.key, role.key
                )
            )
        self.members.check_array_compatible_with_entity(array)
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype=array.dtype)
        if isinstance(array, EnumArray):
            result = EnumArray(result, array.possible_values)
        role_filter = self.members.has_role(role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[members_map][role_filter[members_map]]

        return result

    @projectors.projectable
    def value_nth_person(
        self, n: int, array: ArrayLike, default: Any = 0
    ) -> ArrayLike:
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
        result = self.filled_array(default, dtype=array.dtype)
        # For households that have at least n persons, set the result as the value of criteria for the person for which the position is n.
        # The map is needed b/c the order of the nth persons of each household in the persons vector is not necessarily the same than the household order.
        result[nb_persons_per_entity > n] = array[members_map][
            positions[members_map] == n
        ]

        if isinstance(array, EnumArray):
            result = EnumArray(result, array.possible_values)

        return result

    @projectors.projectable
    def value_from_first_person(self, array: ArrayLike):
        return self.value_nth_person(0, array)

    # Projection entity -> person(s)

    def project(self, array: ArrayLike, role: Role = None) -> ArrayLike:
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)
        if role is None:
            return array[self.members_entity_id]
        else:
            role_condition = self.members.has_role(role)
            return numpy.where(
                role_condition, array[self.members_entity_id], 0
            )
