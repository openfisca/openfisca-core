from __future__ import annotations

from collections.abc import KeysView, MutableMapping

import os
import shutil

import numpy

from openfisca_core import periods
from openfisca_core.indexed_enums import EnumArray
from openfisca_core.periods import DateUnit

from . import types as t


class OnDiskStorage:
    """Storing and retrieving calculated vectors on disk.

    Args:
        storage_dir: Path to store calculated vectors.
        is_eternal: Whether the storage is eternal.
        preserve_storage_dir: Whether to preserve the storage directory.

    """

    #: A dictionary containing data that has been stored on disk.
    storage_dir: str

    #: Whether the storage is eternal.
    is_eternal: bool

    #: Whether to preserve the storage directory.
    preserve_storage_dir: bool

    #: Mapping of file paths to possible :class:`.Enum` values.
    _enums: MutableMapping[str, type[t.Enum]]

    #: Mapping of periods to file paths.
    _files: MutableMapping[t.Period, str]

    def __init__(
        self,
        storage_dir: str,
        is_eternal: bool = False,
        preserve_storage_dir: bool = False,
        enums: MutableMapping[str, type[t.Enum]] | None = None,
    ) -> None:
        self._files = {}
        self._enums = {} if enums is None else enums
        self.is_eternal = is_eternal
        self.preserve_storage_dir = preserve_storage_dir
        self.storage_dir = storage_dir

    def _decode_file(self, file: str) -> t.Array[t.DTypeGeneric]:
        """Decode a file by loading its contents as a :mod:`numpy` array.

        Args:
            file: Path to the file to be decoded.

        Returns:
            EnumArray: Representing the data in the file.
            ndarray[generic]: Representing the data in the file.

        Note:
            If the file is associated with :class:`~indexed_enums.Enum` values, the
            array is converted back to an :obj:`~indexed_enums.EnumArray` object.

        Examples:
            >>> import tempfile

            >>> import numpy

            >>> from openfisca_core import data_storage, indexed_enums, periods

            >>> class Housing(indexed_enums.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"
            ...     FREE_LODGER = "Free lodger"
            ...     HOMELESS = "Homeless"

            >>> array = numpy.array([1])
            >>> value = indexed_enums.EnumArray(array, Housing)
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage._decode_file(storage._files[period])
            EnumArray([Housing.TENANT])

        """
        enum = self._enums.get(self.storage_dir)

        if enum is not None:
            return EnumArray(numpy.load(file), enum)

        array: t.Array[t.DTypeGeneric] = numpy.load(file)

        return array

    def get(self, period: None | t.Period = None) -> None | t.Array[t.DTypeGeneric]:
        """Retrieve the data for the specified period from disk.

        Args:
            period: The period for which data should be retrieved.

        Returns:
            None: If no data is available.
            EnumArray: Representing the data for the specified period.
            ndarray[generic]: Representing the data for the specified period.

        Examples:
            >>> import tempfile

            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

        """
        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        values = self._files.get(period)
        if values is None:
            return None
        return self._decode_file(values)

    def put(self, value: t.Array[t.DTypeGeneric], period: None | t.Period) -> None:
        """Store the specified data on disk for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> import tempfile

            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> value = numpy.array([1, "2", "salary"])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array(['1', '2', 'salary'], ...)

        """
        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        filename = str(period)
        path = os.path.join(self.storage_dir, filename) + ".npy"
        if isinstance(value, EnumArray) and value.possible_values is not None:
            self._enums[self.storage_dir] = value.possible_values
            value = value.view(numpy.ndarray)
        numpy.save(path, value)
        self._files[period] = path

    def delete(self, period: None | t.Period = None) -> None:
        """Delete the data for the specified period from disk.

        Args:
            period: The period for which data should be deleted. If not
                specified, all data will be deleted.

        Examples:
            >>> import tempfile

            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage.delete(period)
            ...     storage.get(period)

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put(value, period)
            ...     storage.delete()
            ...     storage.get(period)

        """
        if period is None:
            self._files = {}
            return

        if self.is_eternal:
            period = periods.period(DateUnit.ETERNITY)
        period = periods.period(period)

        self._files = {
            period_item: value
            for period_item, value in self._files.items()
            if not period.contains(period_item)
        }

    def get_known_periods(self) -> KeysView[t.Period]:
        """List of storage's known periods.

        Returns:
            KeysView[Period]: A sequence containing the storage's known periods.

        Examples:
            >>> import tempfile

            >>> from openfisca_core import data_storage, periods

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.get_known_periods()
            dict_keys([])

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = data_storage.OnDiskStorage(directory)
            ...     storage.put([], period)
            ...     storage.get_known_periods()
            dict_keys([Period(('year', Instant((2017, 1, 1)), 1))])

        """
        return self._files.keys()

    def restore(self) -> None:
        """Restore the storage from disk.

        Examples:
            >>> import tempfile

            >>> import numpy

            >>> from openfisca_core import data_storage, periods

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))
            >>> directory = tempfile.TemporaryDirectory()

            >>> storage1 = data_storage.OnDiskStorage(directory.name)
            >>> storage1.put(value, period)
            >>> storage1._files
            {Period(('year', Instant((2017, 1, 1)), 1)): '...2017.npy'}

            >>> storage2 = data_storage.OnDiskStorage(directory.name)
            >>> storage2._files
            {}

            >>> storage2.restore()
            >>> storage2._files
            {Period((<DateUnit.YEAR: 'year'>, Instant((2017, 1, 1...2017.npy'}

            >>> directory.cleanup()

        """
        self._files = files = {}
        # Restore self._files from content of storage_dir.
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith(".npy"):
                continue
            path = os.path.join(self.storage_dir, filename)
            filename_core = filename.rsplit(".", 1)[0]
            period = periods.period(filename_core)
            files[period] = path

    def __del__(self) -> None:
        if self.preserve_storage_dir:
            return
        shutil.rmtree(self.storage_dir)  # Remove the holder temporary files
        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.storage_dir, os.pardir))
        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)


__all__ = ["OnDiskStorage"]
