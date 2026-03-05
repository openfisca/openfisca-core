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
        """Project or pass through result so it matches source (person) count.

        - Entity-sized (result.size == target.count): same as old logic — project
          to source so each person gets their entity's value (e.g. first_person).
        - Members-sized (result.size == target.members.count): return as-is;
          result is already one value per person (e.g. members('activite')).
        """
        target = self._target_population
        if result.size == target.count:
            return target.project(result)
        if result.size == target.members.count:
            return result
        raise ValueError(
            f"Implicit link projection: result size {result.size} does not match "
            f"target entity count ({target.count}) nor target members count ({target.members.count})."
        )


class ImplicitOne2ManyLink(One2ManyLink):
    """A group → person link using GroupPopulation's internal arrays."""

    def __init__(self, name: str, group_entity_key: str, person_entity_key: str):
        super().__init__(
            name=name,
            link_field="",  # Not used
            target_entity_key=person_entity_key,
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
            # roles may be an object array of Role instances, so compare by key
            if roles.dtype == object:
                try:
                    keys = numpy.fromiter(
                        (getattr(x, "key", x) for x in roles),
                        dtype=object,
                    )
                except Exception:
                    mask &= roles == role
                else:
                    mask &= keys == role
            else:
                mask &= roles == role

        if condition is not None:
            mask &= condition

        source_rows = source_rows[mask]
        values = values[mask]

        valid = source_rows >= 0
        return source_rows[valid], values[valid]

    # override to avoid relying on ``role_field`` which is meaningless for
    # implicit links (the role information is stored on the source population)
    def get_by_role(
        self,
        variable_name: str,
        period,
        role_value,
        *,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Fetch value for a specific role value on a one-to-many implicit link.

        This mirrors :meth:`One2ManyLink.get_by_role` but uses
        ``self._source_population.members_role`` instead of a named role field
        on the target population.
        """
        values = self._target_population.simulation.calculate(variable_name, period)
        source_rows, values = self._apply_filters(period, values, role_value, condition)

        result = numpy.zeros(self._source_population.count, dtype=values.dtype)
        # last value wins (same semantics as GroupPopulation.value_from_person)
        for tgt_idx, src in enumerate(source_rows):
            if src >= 0:
                result[src] = values[tgt_idx]
        return result


__all__ = ["ImplicitMany2OneLink", "ImplicitOne2ManyLink"]
