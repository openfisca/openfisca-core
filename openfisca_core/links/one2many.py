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
            period, values, role, condition,
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
            period, ones, role, condition,
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
            period, values, role, condition,
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
            period, values, role, condition,
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
            period, values, role, condition,
        )
        result = numpy.full(
            self._source_population.count, numpy.inf, dtype=float,
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
            period, values, role, condition,
        )
        result = numpy.full(
            self._source_population.count, -numpy.inf, dtype=float,
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

    # -- internal -----------------------------------------------------------

    def _target_values(
        self, variable_name: str, period,
    ) -> numpy.ndarray:
        """Compute the variable on the target entity."""
        return self._target_population.simulation.calculate(
            variable_name, period,
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

        # Role filter
        if role is not None and self.role_field is not None:
            simulation = self._target_population.simulation
            roles = simulation.calculate(self.role_field, "eternity")
            mask = roles == role
            source_rows = source_rows[mask]
            values = values[mask]

        # Condition filter
        if condition is not None:
            source_rows = source_rows[condition]
            values = values[condition]

        # Remove invalid rows
        valid = source_rows >= 0
        return source_rows[valid], values[valid]


__all__ = ["One2ManyLink"]
