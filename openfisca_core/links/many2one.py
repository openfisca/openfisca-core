"""Many-to-one link: N source members → 1 target entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy

from .link import Link

if TYPE_CHECKING:
    pass


class Many2OneLink(Link):
    """Navigate from many source members to one target entity.

    Example: ``person.household`` (each person belongs to one household),
    or ``person.mother`` (each person has one mother).

    The resolution follows the LIAM2 pattern::

        target_ids = source_pop(link_field)     # e.g. [0, 0, 1, 2, 0]
        target_values = target_pop(variable)    # e.g. [800, 650, 900]
        result = target_values[target_ids]      # e.g. [800, 800, 650, 900, 800]
    """

    def get(self, variable_name: str, period) -> numpy.ndarray:
        """Get a target variable's value for each source member.

        Parameters
        ----------
        variable_name : str
            Name of the variable defined on the target entity.
        period : Period
            The period for which to compute the variable.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_source,)`` containing the target variable
            value for each source member.  Members with an invalid link
            (target_id < 0) receive the variable's default value.
        """
        source_pop = self._source_population
        target_pop = self._target_population
        simulation = source_pop.simulation

        # 1. Target IDs for each source member
        target_ids = simulation.calculate(self.link_field, period)

        # 2. Variable values on the target entity
        target_values = simulation.calculate(variable_name, period)

        # 3. Resolve IDs to row positions (handles id_to_rownum if needed)
        target_rows = self._resolve_ids(target_ids)

        # 4. Gather with missing-value handling
        variable = simulation.tax_benefit_system.get_variable(variable_name)
        default = variable.default_value if variable else 0
        result = numpy.full(
            source_pop.count,
            default,
            dtype=target_values.dtype,
        )
        valid = target_rows >= 0
        result[valid] = target_values[target_rows[valid]]
        return result

    # -- syntactic sugar ----------------------------------------------------

    def __call__(self, variable_name: str, period) -> numpy.ndarray:
        """Shorthand: ``person.mother("age", period)``."""
        return self.get(variable_name, period)

    def __getattr__(self, name: str):
        """Chain links: ``person.mother.household``."""
        if name.startswith("_"):
            raise AttributeError(name)
        target_entity = self._target_population.entity
        target_link = _find_link(target_entity, name)
        if target_link is not None:
            return _ChainedGetter(self, target_link)
        msg = (
            f"Entity '{target_entity.key}' has no link named '{name}'"
        )
        raise AttributeError(msg)

    # -- role helpers -------------------------------------------------------

    @property
    def role(self) -> numpy.ndarray | None:
        """Role of each source member, if ``role_field`` is set."""
        if self.role_field is None:
            return None
        return self._source_population.simulation.calculate(
            self.role_field,
            "eternity",
        )

    def has_role(self, role_value) -> numpy.ndarray:
        """Boolean mask: does each source member have the given role?"""
        r = self.role
        if r is None:
            msg = f"Link '{self.name}' has no role_field"
            raise ValueError(msg)
        return r == role_value

    # -- ID resolution ------------------------------------------------------

    def _resolve_ids(self, target_ids: numpy.ndarray) -> numpy.ndarray:
        """Convert target IDs to row indices.

        If the target population has an ``_id_to_rownum`` mapping
        (e.g. for intra-entity links where IDs ≠ row positions), use it.
        Otherwise treat IDs as direct row indices (the OpenFisca convention
        for GroupPopulation.members_entity_id).
        """
        target_pop = self._target_population
        rows = numpy.full_like(target_ids, -1, dtype=numpy.intp)

        if hasattr(target_pop, "_id_to_rownum") and target_pop._id_to_rownum is not None:
            id_to_rownum = target_pop._id_to_rownum
            valid = (target_ids >= 0) & (target_ids < len(id_to_rownum))
            rows[valid] = id_to_rownum[target_ids[valid]]
        else:
            valid = (target_ids >= 0) & (target_ids < target_pop.count)
            rows[valid] = target_ids[valid]

        return rows


# ---------------------------------------------------------------------------
# Chained link getter
# ---------------------------------------------------------------------------

class _ChainedGetter:
    """Intermediate object for link chaining: ``person.mother.household``."""

    def __init__(self, outer_link: Many2OneLink, inner_link: Link) -> None:
        self._outer = outer_link
        self._inner = inner_link

    def __call__(self, variable_name: str, period) -> numpy.ndarray:
        """Resolve ``person.mother.household("rent", period)``."""
        # 1. Resolve inner link value on inner entity
        inner_values = self._inner.get(variable_name, period)

        # 2. Map back through outer link
        target_ids = self._outer._source_population.simulation.calculate(
            self._outer.link_field, period,
        )
        target_rows = self._outer._resolve_ids(target_ids)

        result = numpy.full(
            self._outer._source_population.count,
            0,
            dtype=inner_values.dtype,
        )
        valid = target_rows >= 0
        result[valid] = inner_values[target_rows[valid]]
        return result

    def __getattr__(self, name: str):
        """Continue chaining: ``person.mother.household.region``."""
        if name.startswith("_"):
            raise AttributeError(name)
        target_entity = self._inner._target_population.entity
        next_link = _find_link(target_entity, name)
        if next_link is not None:
            return _ChainedGetter(self._outer, next_link)
        raise AttributeError(
            f"Entity '{target_entity.key}' has no link named '{name}'"
        )


def _find_link(entity, name: str) -> Link | None:
    """Look up a link by name on an entity."""
    links = getattr(entity, "_links", None)
    if links is None:
        return None
    return links.get(name)


__all__ = ["Many2OneLink"]
