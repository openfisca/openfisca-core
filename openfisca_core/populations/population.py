from __future__ import annotations

import numpy

from openfisca_core import projectors

from . import types as t
from ._core_population import CorePopulation


class Population(CorePopulation):
    def __init__(self, entity: t.Entity) -> None:
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

        if attribute.startswith("nb_"):
            role = attribute[3:]
            if role in self._roles_to_memberships:
                membership = self._roles_to_memberships[role]
                return membership.nb_members(role)
            else:
                return self.single_membership.nb_members

        msg = f"You tried to use the '{attribute}' of '{self.entity.key}' but that is not a known attribute."
        raise AttributeError(
            msg,
        )

    # Helpers

    @projectors.projectable
    def has_role(self, role: t.Role) -> None | t.BoolArray:
        """Check if a person has a given role within its `Entity`.

        Example:
        >>> person.has_role(Household.CHILD)
        >>> array([False])

        """
        if self.simulation is None:
            return None
        self.entity.check_role_validity(role)

        membership = self._roles_to_memberships[role.key]

        if role.subroles:
            return numpy.logical_or.reduce(
                [membership.members_role == subrole for subrole in role.subroles],
            )

        return membership.members_role == role

    @property
    def members(self):
        return self.single_membership.members

    @property
    def single_membership(self):
        if len(self._memberships) > 1:
            raise ValueError("Too many memberships")

        return self._memberships[0]

    @projectors.projectable
    def value_from_partner(
        self,
        array: t.FloatArray,
        entity: projectors.Projector,
        role: t.Role,
    ) -> None | t.FloatArray:
        return self.single_membership.value_nth_person(array, entity, role)

    @projectors.projectable
    def value_nth_person(self, n, array, default=0):
        return self.single_membership.value_nth_person(n, array, default)

    @projectors.projectable
    def value_from_first_person(self, array):
        return self.single_membership.value_from_first_person(array)

    @projectors.projectable
    def sum(self, array, role=None):
        return self.single_membership.sum(array, role)

    @projectors.projectable
    def max(self, array, role=None):
        return self.single_membership.max(array, role)

    @projectors.projectable
    def any(self, array, role=None):
        return self.single_membership.any(array, role)

    @projectors.projectable
    def all(self, array, role=None):
        return self.single_membership.all(array, role)

    @projectors.projectable
    def min(self, array, role=None):
        return self.single_membership.min(array, role)

    @projectors.projectable
    def project(self, array, role=None):
        return self.single_membership.project(array, role)

    @projectors.projectable
    def get_rank(
        self,
        entity: Population,
        criteria: t.FloatArray,
        condition: bool = True,
    ) -> t.IntArray:
        return self.single_membership.get_rank(entity, criteria, condition)