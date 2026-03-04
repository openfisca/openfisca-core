"""Implicit links dynamically inferred from OpenFisca's GroupPopulation system."""

from __future__ import annotations

import numpy

from .many2one import Many2OneLink
from .one2many import One2ManyLink


class ImplicitMany2OneLink(Many2OneLink):
    """A person → group link using GroupPopulation's internal arrays.

    This bypasses the usual Variable lookup (``simulation.calculate``)
    and directly reads ``members_entity_id`` and ``members_role`` from
    the target GroupPopulation.
    """

    def __init__(self, group_entity_key: str):
        super().__init__(
            name=group_entity_key,
            link_field="",  # Not used
            target_entity_key=group_entity_key,
        )

    def _get_target_ids(self, period) -> numpy.ndarray:
        return self._target_population.members_entity_id

    @property
    def role(self) -> numpy.ndarray | None:
        return self._target_population.members_role

    def _project_implicit(self, result: numpy.ndarray) -> numpy.ndarray:
        # Fully compatible with old Projector logic
        return self._target_population.project(result)


class ImplicitOne2ManyLink(One2ManyLink):
    """A group → person link using GroupPopulation's internal arrays."""

    def __init__(self, name: str, group_entity_key: str):
        super().__init__(
            name=name,
            link_field="",  # Not used
            target_entity_key="person",  # The target of the O2M is persons
        )
        self._group_entity_key = group_entity_key

    def _source_rows(self, period) -> numpy.ndarray:
        # For a group->person O2M, the source is the group, the target is the person.
        # members_entity_id is an array of length person.count, containing the group index.
        # So members_entity_id IS the array of source rows for each target member.
        return self._source_population.members_entity_id

    def _apply_filters(self, period, values, role, condition):
        source_rows = self._source_rows(period)
        mask = numpy.ones(len(source_rows), dtype=bool)

        if role is not None:
            roles = self._source_population.members_role
            mask &= roles == role

        if condition is not None:
            mask &= condition

        source_rows = source_rows[mask]
        values = values[mask]

        valid = source_rows >= 0
        return source_rows[valid], values[valid]


__all__ = ["ImplicitMany2OneLink", "ImplicitOne2ManyLink"]
