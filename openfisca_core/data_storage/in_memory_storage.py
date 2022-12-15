from __future__ import annotations

from openfisca_core.types import Period
from typing import Optional, Sequence

import numpy

from openfisca_core import periods

from . import _funcs
from ._arrays import Arrays
from .typing import MemoryUsage


class InMemoryStorage:
    """Class responsible for storing/retrieving vectors in/from memory.

    Attributes:
        _arrays: A dictionary containing data that has been stored in memory.
        is_eternal: Flag indicating if the storage of period eternity.

    Args:
        is_eternal: Flag indicating if the storage of period eternity.

    """

    _arrays: Arrays = Arrays({})

    def __init__(self, is_eternal: bool = False) -> None:
        self.is_eternal = is_eternal

    def get(self, period: Period) -> Optional[numpy.ndarray]:
        """Retrieve the data for the specified period from memory.

        Args:
            period: The period for which data should be retrieved.

        Returns:
            The data for the specified period, or None if no data is available.

        Examples:
            >>> storage = InMemoryStorage()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

        """

        period = _funcs.parse_period(period, self.is_eternal)
        values = self._arrays.get(period)

        if values is None:
            return None

        return values

    def put(self, value: numpy.ndarray, period: Period) -> None:
        """Store the specified data in memory for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> storage = InMemoryStorage()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

        """

        period = _funcs.parse_period(period, self.is_eternal)
        self._arrays = Arrays({period: value, **self._arrays})

    def delete(self, period: Optional[Period] = None) -> None:
        """Delete the data for the specified period from memory.

        Args:
            period: The period for which data should be deleted. If not
                specified, all data will be deleted.

        Examples:
            >>> storage = InMemoryStorage()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

            >>> storage.delete(period)

            >>> storage.get(period)

            >>> storage.put(value, period)

            >>> storage.delete()

            >>> storage.get(period)

        """

        if period is None:
            self._arrays = Arrays({})
            return None

        period = _funcs.parse_period(period, self.is_eternal)

        self._arrays = Arrays({
            key: value
            for key, value in self._arrays.items()
            if not period.contains(key)
            })

    def periods(self) -> Sequence[Period]:
        """List of storage's known periods.

        Returns:
            A sequence containing the storage's known periods.

        Examples:
            >>> storage = InMemoryStorage()

            >>> storage.periods()
            []

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))
            >>> storage.put([], period)
            >>> storage.periods()
            [Period(('year', Instant((2017, 1, 1)), 1))]

        """

        return list(self._arrays.keys())

    def usage(self) -> MemoryUsage:
        """Memory usage of the storage.

        Returns:
            A dictionary representing the storage's memory usage.

        Examples:
            >>> storage = InMemoryStorage()

            >>> storage.usage()
            {'cell_size': nan, 'nb_arrays': 0, 'total_nb_bytes': 0}

        """

        if not self._arrays:
            return MemoryUsage(
                cell_size = numpy.nan,
                nb_arrays = 0,
                total_nb_bytes = 0,
                )

        nb_arrays = len(self._arrays)
        array = next(iter(self._arrays.values()))
        total = array.nbytes * nb_arrays

        return MemoryUsage(
            cell_size = array.itemsize,
            nb_arrays = nb_arrays,
            total_nb_bytes = total,
            )
