from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy

from openfisca_core import periods, types

from . import _funcs
from ._arrays import Arrays


class InMemoryStorage:
    """Class responsible for storing/retrieving vectors in/from memory.

    Attributes:
        _arrays: ?
        is_eternal: ?

    Args:
        is_eternal: ?

    """

    _arrays: Arrays

    def __init__(self, is_eternal: bool = False) -> None:
        self._arrays = Arrays({})
        self.is_eternal = is_eternal

    def get(self, period: types.Period) -> Any:
        period = _funcs.parse_period(period, self.is_eternal)
        values = self._arrays.get(period)

        if values is None:
            return None

        return values

    def put(self, value: Any, period: types.Period) -> None:
        period = _funcs.parse_period(period, self.is_eternal)
        self._arrays = Arrays({period: value, **self._arrays})

    def delete(self, period: Optional[types.Period] = None) -> None:
        if period is None:
            self._arrays = Arrays({})
            return None

        period = _funcs.parse_period(period, self.is_eternal)

        self._arrays = Arrays({
            period_item: value
            for period_item, value in self._arrays.items()
            if not period.contains(period_item)
            })

    def get_known_periods(self) -> Sequence[types.Period]:
        """List of storage's known periods.

        Returns:
            A list of periods.

        Examples:
            >>> storage = InMemoryStorage()

            >>> storage.get_known_periods()
            []

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))
            >>> storage.put([], period)
            >>> storage.get_known_periods()
            [Period(('year', Instant((2017, 1, 1)), 1))]

        """

        return list(self._arrays.keys())

    def get_memory_usage(self) -> types.MemoryUsage:
        """Memory usage of the storage.

        Returns:
            A dictionary representing the memory usage.

        Examples:
            >>> storage = InMemoryStorage()
            >>> storage.get_memory_usage()
            {'cell_size': nan, 'nb_arrays': 0, 'total_nb_bytes': 0}

        """

        if not self._arrays:
            return types.MemoryUsage(
                cell_size = numpy.nan,
                nb_arrays = 0,
                total_nb_bytes = 0,
                )

        nb_arrays = len(self._arrays)
        array = next(iter(self._arrays.values()))
        total = array.nbytes * nb_arrays

        return types.MemoryUsage(
            cell_size = array.itemsize,
            nb_arrays = nb_arrays,
            total_nb_bytes = total,
            )
