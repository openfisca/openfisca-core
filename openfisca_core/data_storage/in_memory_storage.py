import numpy

from openfisca_core import periods
from openfisca_core.periods import DateUnit


class InMemoryStorage:
    """Storing and retrieving calculated vectors in memory.

    Args:
        is_eternal: Whether the storage is eternal.

    """

    #: Whether the storage is eternal.
    is_eternal: bool

    #: A dictionary containing data that has been stored in memory.
    _arrays: dict

    def __init__(self, is_eternal=False) -> None:
        self._arrays = {}
        self.is_eternal = is_eternal

    def get(self, period):
        """Retrieve the data for the specified period from memory.

        Args:
            period: The period for which data should be retrieved.

        Returns:
            The data for the specified period, or None if no data is available.

        Examples:
            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> storage = data_storage.InMemoryStorage()
            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array([1, 2, 3])

        """

        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        values = self._arrays.get(period)
        if values is None:
            return None
        return values

    def put(self, value, period) -> None:
        """Store the specified data in memory for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> storage = data_storage.InMemoryStorage()
            >>> value = numpy.array([1, "2", "salary"])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> storage.put(value, period)

            >>> storage.get(period)
            array(['1', '2', 'salary'], dtype='<U21')

        """

        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        self._arrays[period] = value

    def delete(self, period=None) -> None:
        """Delete the data for the specified period from memory.

        Args:
            period: The period for which data should be deleted.

        Note:
            If ``period`` is specified, all data will be deleted.

        Examples:
            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> storage = data_storage.InMemoryStorage()
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
            self._arrays = {}
            return

        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        self._arrays = {
            period_item: value
            for period_item, value in self._arrays.items()
            if not period.contains(period_item)
        }

    def get_known_periods(self):
        """List of storage's known periods.

        Returns:
            A sequence containing the storage's known periods.

        Examples:
            >>> from openfisca_core import data_storage, periods

            >>> storage = data_storage.InMemoryStorage()
            >>> storage.get_known_periods()
            dict_keys([])

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))
            >>> storage.put([], period)

            >>> storage.get_known_periods()
            dict_keys([Period(('year', Instant((2017, 1, 1)), 1))])

        """

        return self._arrays.keys()

    def get_memory_usage(self):
        """Memory usage of the storage.

        Returns:
            A dictionary representing the storage's memory usage.

        Examples:
            >>> from openfisca_core import data_storage

            >>> storage = data_storage.InMemoryStorage()
            >>> storage.get_memory_usage()
            {'nb_arrays': 0, 'total_nb_bytes': 0, 'cell_size': nan}

        """

        if not self._arrays:
            return {
                "nb_arrays": 0,
                "total_nb_bytes": 0,
                "cell_size": numpy.nan,
            }

        nb_arrays = len(self._arrays)
        array = next(iter(self._arrays.values()))
        return {
            "nb_arrays": nb_arrays,
            "total_nb_bytes": array.nbytes * nb_arrays,
            "cell_size": array.itemsize,
        }
