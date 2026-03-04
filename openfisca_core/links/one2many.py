"""One-to-many link: 1 source entity → N target members."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy

from .link import Link

if TYPE_CHECKING:
    pass


class One2ManyLink(Link):
    """Aggregate from many target members back to one source entity.

    Example: ``household.members`` (one household has many persons).

    Provides aggregation methods (sum, count, any, all, min, max) that
    combine values from all targets belonging to each source, optionally
    filtered by role or an arbitrary boolean condition.
    """

    # -- aggregation methods ------------------------------------------------

    def sum(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Sum target values grouped by source entity.

        Equivalent to ``GroupPopulation.sum(array, role=role)``.
        """
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(
            period,
            values,
            role,
            condition,
        )
        return numpy.bincount(
            source_rows,
            weights=values.astype(float),
            minlength=self._source_population.count,
        )

    def count(
        self,
        period=None,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Count target members per source entity.

        Equivalent to ``GroupPopulation.nb_persons(role=role)``.
        """
        ones = numpy.ones(self._target_population.count)
        source_rows, ones = self._apply_filters(
            period,
            ones,
            role,
            condition,
        )
        return numpy.bincount(
            source_rows,
            weights=ones,
            minlength=self._source_population.count,
        ).astype(int)

    def any(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """True if any target member has a truthy value."""
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(
            period,
            values,
            role,
            condition,
        )
        result = numpy.zeros(self._source_population.count, dtype=bool)
        numpy.logical_or.at(result, source_rows, values.astype(bool))
        return result

    def all(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """True if all target members have a truthy value."""
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(
            period,
            values,
            role,
            condition,
        )
        result = numpy.ones(self._source_population.count, dtype=bool)
        numpy.logical_and.at(result, source_rows, values.astype(bool))
        return result

    def min(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Minimum target value per source entity."""
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(
            period,
            values,
            role,
            condition,
        )
        result = numpy.full(
            self._source_population.count,
            numpy.inf,
            dtype=float,
        )
        numpy.minimum.at(result, source_rows, values.astype(float))
        result[result == numpy.inf] = 0
        return result

    def max(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Maximum target value per source entity."""
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(
            period,
            values,
            role,
            condition,
        )
        result = numpy.full(
            self._source_population.count,
            -numpy.inf,
            dtype=float,
        )
        numpy.maximum.at(result, source_rows, values.astype(float))
        result[result == -numpy.inf] = 0
        return result

    def avg(
        self,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Average target value per source entity."""
        s = self.sum(variable_name, period, role=role, condition=condition)
        c = self.count(period, role=role, condition=condition)
        return numpy.where(c > 0, s / c, 0)

    # -- positional and role-based accessors --------------------------------

    def nth(
        self,
        n: int,
        variable_name: str,
        period,
        *,
        role=None,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Value of the n-th target member for each source entity.

        Parameters mirror :meth:`sum` plus ``n``.  If a source has fewer than
        ``n+1`` targets the default value ``0`` is returned for that source.
        The ordering of targets is the same as encountered in the underlying
        population arrays (i.e. no particular sort).
        """
        values = self._target_values(variable_name, period)
        source_rows, values = self._apply_filters(period, values, role, condition)

        result = numpy.zeros(self._source_population.count, dtype=values.dtype)
        # collect indices per source and pick the n-th
        for src in range(self._source_population.count):
            idxs = numpy.nonzero(source_rows == src)[0]
            if n < len(idxs):
                result[src] = values[idxs[n]]
        return result

    def get_by_role(
        self,
        variable_name: str,
        period,
        role_value,
        *,
        condition: numpy.ndarray | None = None,
    ) -> numpy.ndarray:
        """Value of the target having a unique role per source.

        ``role_value`` is compared against the ``role_field`` on the target
        population.  If multiple targets share the same role for a given source
        the last encountered value is returned (behaviour mirrors
        ``GroupPopulation.value_from_person``).
        """
        if self.role_field is None:
            raise ValueError("Link has no role_field")

        values = self._target_values(variable_name, period)
        source_rows = self._source_rows(period)
        roles = self._target_population.simulation.calculate(
            self.role_field,
            "eternity",
        )

        result = numpy.zeros(self._source_population.count, dtype=values.dtype)
        mask = numpy.ones(len(source_rows), dtype=bool)
        if condition is not None:
            mask &= condition

        for tgt_idx, src in enumerate(source_rows[mask]):
            if roles[mask][tgt_idx] == role_value and src >= 0:
                result[src] = values[mask][tgt_idx]
        return result

    # -- internal -----------------------------------------------------------

    def _target_values(
        self,
        variable_name: str,
        period,
    ) -> numpy.ndarray:
        """Compute the variable on the target entity."""
        return self._target_population.simulation.calculate(
            variable_name,
            period,
        )

    def _source_rows(self, period) -> numpy.ndarray:
        """For each target member, the row index of its source entity.

        This reads ``link_field`` from the *target* population (the members)
        and resolves to source row indices.
        """
        target_pop = self._target_population
        source_pop = self._source_population
        simulation = target_pop.simulation

        source_ids = simulation.calculate(self.link_field, period)

        # If source has id_to_rownum, use it; else IDs are positions.
        if (
            hasattr(source_pop, "_id_to_rownum")
            and source_pop._id_to_rownum is not None
        ):
            id_to_rownum = source_pop._id_to_rownum
            rows = numpy.full_like(source_ids, -1, dtype=numpy.intp)
            valid = (source_ids >= 0) & (source_ids < len(id_to_rownum))
            rows[valid] = id_to_rownum[source_ids[valid]]
            return rows

        rows = source_ids.copy().astype(numpy.intp)
        rows[(rows < 0) | (rows >= source_pop.count)] = -1
        return rows

    def _apply_filters(self, period, values, role, condition):
        """Apply role and condition filters, return (source_rows, values)."""
        source_rows = self._source_rows(period)
        mask = numpy.ones(len(source_rows), dtype=bool)

        # Role filter
        if role is not None and self.role_field is not None:
            simulation = self._target_population.simulation
            roles = simulation.calculate(self.role_field, "eternity")
            mask &= roles == role

        # Condition filter
        if condition is not None:
            mask &= condition

        source_rows = source_rows[mask]
        values = values[mask]

        # Remove invalid rows
        valid = source_rows >= 0
        return source_rows[valid], values[valid]


__all__ = ["One2ManyLink"]
