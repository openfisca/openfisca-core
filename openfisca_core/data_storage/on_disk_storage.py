from __future__ import annotations

from typing import Any, NoReturn, Optional, Sequence, Union

import os
import pathlib
import shutil

import numpy

from openfisca_core import periods, indexed_enums as enums, types

from . import _funcs
from ._enums import Enums
from ._files import Files


class OnDiskStorage:
    """Class responsible for storing/retrieving vectors on/from disk.

    Attributes:
        _enums: Mapping of file paths to possible Enum values.
        _files: Mapping of periods to file paths for stored vectors.
        is_eternal: Flag indicating if the storage of period eternity.
        preserve_storage_dir: Flag indicating if folders should be preserved.
        storage_dir: Path to store calculated vectors.

    Args:
        storage_dir: Path to store calculated vectors.
        is_eternal: Flag indicating if the storage of period eternity.
        preserve_storage_dir: Flag indicating if folders should be preserved.

    """

    _enums: Enums = Enums({})
    _files: Files = Files({})
    is_eternal: bool
    storage_dir: str
    preserve_storage_dir: bool

    def __init__(
            self,
            storage_dir: str,
            is_eternal: bool = False,
            preserve_storage_dir: bool = False,
            ) -> None:
        self.is_eternal = is_eternal
        self.storage_dir = storage_dir
        self.preserve_storage_dir = preserve_storage_dir

    def _decode_file(self, file: str) -> Any:
        """Decodes a file by loading its contents as a NumPy array.

        If the file is associated with Enum values, the array is converted back
        to an EnumArray object.

        Args:
            file: Path to the file to be decoded.

        Returns:
            NumPy array or EnumArray object representing the data in the file.

        Examples
            >>> import tempfile

            >>> class Housing(enums.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"
            ...     FREE_LODGER = "Free lodger"
            ...     HOMELESS = "Homeless"

            >>> array = numpy.array([1])
            >>> value = enums.EnumArray(array, Housing)
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage._decode_file(storage._files[period])
            EnumArray([<Housing.TENANT: 'Tenant'>])

        """

        enum = self._enums.get(file)
        load = numpy.load(file)

        if enum is None:
            return load

        return enums.EnumArray(load, enum)

    def get(
            self,
            period: types.Period,
            ) -> Optional[Union[numpy.ndarray, enums.EnumArray]]:
        """Retrieve the data for the specified period from disk.

        Args:
            period: The period for which data should be retrieved.

        Returns:
            A NumPy array or EnumArray object representing the vector for the
            specified period, or None if no vector is stored for that period.

        Examples:
            >>> import tempfile

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

        """

        period = _funcs.parse_period(period, self.is_eternal)
        values = self._files.get(period)

        if values is None:
            return None

        return self._decode_file(values)

    def put(self, value: Any, period: types.Period) -> None:
        """Store the specified data on disk for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> import tempfile

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

        """

        period = _funcs.parse_period(period, self.is_eternal)
        stem = str(period)
        path = os.path.join(self.storage_dir, f"{stem}.npy")

        if isinstance(value, enums.EnumArray):
            self._enums = Enums({path: value.possible_values, **self._enums})
            value = value.view(numpy.ndarray)

        numpy.save(path, value)
        self._files = Files({period: path, **self._files})

    def delete(self, period: Optional[types.Period] = None) -> None:
        """Delete the data for the specified period from disk.

        Args:
            period: The period for which data should be deleted. If not
                specified, all data will be deleted.

        Examples:
            >>> import tempfile

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage.delete(period)
            ...     storage.get(period)

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put(value, period)
            ...     storage.delete()
            ...     storage.get(period)

        """

        if period is None:
            self._files = Files({})
            return None

        period = _funcs.parse_period(period, self.is_eternal)

        self._files = Files({
            key: value
            for key, value in self._files.items()
            if not period.contains(key)
            })

    def get_known_periods(self) -> Sequence[types.Period]:
        """List of storage's known periods.

        Returns:
            A sequence containing the storage's known periods.

        Examples:
            >>> import tempfile

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.get_known_periods()
            []

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.put([], period)
            ...     storage.get_known_periods()
            [Period(('year', Instant((2017, 1, 1)), 1))]

        """

        return list(self._files.keys())

    def get_memory_usage(self) -> NoReturn:
        """Memory usage of the storage.

        Raises:
            NotImplementedError: Method not implemented for this storage.

        Examples:
            >>> import tempfile

            >>> with tempfile.TemporaryDirectory() as storage_dir:
            ...     storage = OnDiskStorage(storage_dir)
            ...     storage.get_memory_usage()
            Traceback (most recent call last):
            ...
            NotImplementedError: Method not implemented for this storage.

        .. versionadded:: 37.1.0

        """

        raise NotImplementedError("Method not implemented for this storage.")

    def restore(self) -> None:
        self._files = Files({})
        # Restore self._files from content of storage_dir.
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.npy'):
                continue
            path = os.path.join(self.storage_dir, filename)
            filename_core = filename.rsplit('.', 1)[0]
            period = periods.period(filename_core)
            self._files = Files({period: path, **self._files})

    def __del__(self) -> None:
        if self.preserve_storage_dir:
            return None

        path = pathlib.Path(self.storage_dir)

        if path.exists():
            # Remove the holder temporary files
            shutil.rmtree(self.storage_dir)

        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.storage_dir, os.pardir))

        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)
