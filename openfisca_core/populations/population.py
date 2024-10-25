from __future__ import annotations

import numpy

from openfisca_core import projectors

from . import types as t
from ._core_population import CorePopulation


class Population(CorePopulation):
    def __init__(self, entity: t.SingleEntity) -> None:
        super().__init__(entity)

    def clone(self, simulation: t.Simulation) -> t.CorePopulation:
        result = Population(self.entity)
        result.simulation = simulation
        result._holders = {
            variable: holder.clone(result)
            for (variable, holder) in self._holders.items()
        }
        result.count = self.count
        result.ids = self.ids
        return result

    def __getattr__(self, attribute: str) -> projectors.Projector:
        projector: projectors.Projector | None
        projector = projectors.get_projector_from_shortcut(self, attribute)

        if isinstance(projector, projectors.Projector):
            return projector

        msg = f"You tried to use the '{attribute}' of '{self.entity.key}' but that is not a known attribute."
        raise AttributeError(
            msg,
        )

    # Helpers

    @projectors.projectable
    def has_role(self, role: t.Role) -> None | t.BoolArray:
        """Check if a person has a given role within its `GroupEntity`.

        Example:
        >>> person.has_role(Household.CHILD)
        >>> array([False])

        """
        if self.simulation is None:
            return None

        self.entity.check_role_validity(role)

        group_population = self.simulation.get_population(role.entity.plural)

        if role.subroles:
            return numpy.logical_or.reduce(
                [group_population.members_role == subrole for subrole in role.subroles],
            )

        return group_population.members_role == role

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
        entity: Population,
        criteria: t.FloatArray,
        condition: bool = True,
    ) -> t.IntArray:
        """Get the rank of a person within an entity according to a criteria.
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
        # If entity is for instance 'person.household', we get the reference entity 'household' behind the projector
        entity = (
            entity
            if not isinstance(entity, projectors.Projector)
            else entity.reference_entity
        )

        positions = entity.members_position
        biggest_entity_size = numpy.max(positions) + 1
        filtered_criteria = numpy.where(condition, criteria, numpy.inf)
        ids = entity.members_entity_id

        # Matrix: the value in line i and column j is the value of criteria for the jth person of the ith entity
        matrix = numpy.asarray(
            [
                entity.value_nth_person(k, filtered_criteria, default=numpy.inf)
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
