from __future__ import annotations

from collections.abc import Sequence
from openfisca_core.holders.typing import MemoryUsage
from openfisca_core.types import Period

import numpy

from openfisca_core import periods


class MemoryRepo:
    """Class responsible for storing/retrieving vectors in/from memory."""

    #: A dictionary containing data that has been stored in memory.
    __arrays__: dict[Period, numpy.ndarray] = {}

    def get(self, period: Period) -> numpy.ndarray | None:
        """Retrieve the data for the specified period from memory.

        Args:
            period: The period for which data should be retrieved.

        Returns:
            The data for the specified period, or None if no data is available.

        Examples:
            >>> storage = MemoryRepo()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

        """

        values = self.__arrays__.get(period)

        if values is None:
            return None

        return values

    def put(self, value: numpy.ndarray, period: Period) -> None:
        """Store the specified data in memory for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> storage = MemoryRepo()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

        """

        self.__arrays__ = {period: value, **self.__arrays__}

    def delete(self, period: Period | None = None) -> None:
        """Delete the data for the specified period from memory.

        Args:
            period: The period for which data should be deleted. If not
                specified, all data will be deleted.

        Examples:
            >>> storage = MemoryRepo()
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
            self.__arrays__ = {}
            return None

        self.__arrays__ = {
            key: value
            for key, value in self.__arrays__.items()
            if not period.contains(key)
        }

    def periods(self) -> Sequence[Period]:
        """List of storage's known periods.

        Returns:
            A sequence containing the storage's known periods.

        Examples:
            >>> storage = MemoryRepo()

            >>> storage.periods()
            []

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))
            >>> storage.put([], period)
            >>> storage.periods()
            [Period(('year', Instant((2017, 1, 1)), 1))]

        """

        return list(self.__arrays__.keys())

    def usage(self) -> MemoryUsage:
        """Memory usage of the storage.

        Returns:
            A dictionary representing the storage's memory usage.

        Examples:
            >>> storage = MemoryRepo()

            >>> storage.usage()
            {'cell_size': nan, 'nb_arrays': 0, 'total_nb_bytes': 0}

        """

        if not self.__arrays__:
            return MemoryUsage(
                cell_size=numpy.nan,
                nb_arrays=0,
                total_nb_bytes=0,
            )

        nb_arrays = len(self.__arrays__)
        array = next(iter(self.__arrays__.values()))
        total = array.nbytes * nb_arrays

        return MemoryUsage(
            cell_size=array.itemsize,
            nb_arrays=nb_arrays,
            total_nb_bytes=total,
        )
