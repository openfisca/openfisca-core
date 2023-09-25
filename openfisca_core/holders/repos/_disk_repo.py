from __future__ import annotations

from collections.abc import Sequence
from openfisca_core.types import Enum, Period
from typing import Any, NoReturn

import os
import pathlib
import shutil

import numpy

from openfisca_core import indexed_enums as enums
from openfisca_core import periods


class DiskRepo:
    """Class responsible for storing/retrieving vectors on/from disk.

    Attributes:
        directory: Path to store calculated vectors.
        keep: Flag indicating if folders should be preserved.

    """

    is_eternal: bool
    directory: str
    keep: bool

    #: Mapping of file paths to possible Enum values.
    __enums__: dict[str, type[Enum]] = {}

    #: Mapping of periods to file paths for stored vectors.
    __files__: dict[Period, str] = {}

    def __init__(self, directory: str, keep: bool = False) -> None:
        self.directory = directory
        self.keep = keep

    def get(
        self,
        period: Period,
    ) -> numpy.ndarray | enums.EnumArray | None:
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

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

        """

        values = self.__files__.get(period)

        if values is None:
            return None

        return self._decode_file(values)

    def put(self, value: Any, period: Period) -> None:
        """Store the specified data on disk for the specified period.

        Args:
            value: The data to store
            period: The period for which the data should be stored.

        Examples:
            >>> import tempfile

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

        """

        stem = str(period)
        path = os.path.join(self.directory, f"{stem}.npy")

        if isinstance(value, enums.EnumArray):
            self.__enums__ = {path: value.possible_values, **self.__enums__}
            value = value.view(numpy.ndarray)

        numpy.save(path, value)
        self.__files__ = {period: path, **self.__files__}

    def delete(self, period: Period | None = None) -> None:
        """Delete the data for the specified period from disk.

        Args:
            period: The period for which data should be deleted. If not
                specified, all data will be deleted.

        Examples:
            >>> import tempfile

            >>> value = numpy.array([1, 2, 3])
            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage.get(period)
            array([1, 2, 3])

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage.delete(period)
            ...     storage.get(period)

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage.delete()
            ...     storage.get(period)

        """

        if period is None:
            self.__files__ = {}
            return None

        self.__files__ = {
            key: value
            for key, value in self.__files__.items()
            if not period.contains(key)
        }

    def periods(self) -> Sequence[Period]:
        """List of storage's known periods.

        Returns:
            A sequence containing the storage's known periods.

        Examples:
            >>> import tempfile

            >>> instant = periods.Instant((2017, 1, 1))
            >>> period = periods.Period(("year", instant, 1))

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.periods()
            []

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put([], period)
            ...     storage.periods()
            [Period(('year', Instant((2017, 1, 1)), 1))]

        """

        return list(self.__files__.keys())

    def usage(self) -> NoReturn:
        """Memory usage of the storage.

        Raises:
            NotImplementedError: Method not implemented for this storage.

        Examples:
            >>> import tempfile

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.usage()
            Traceback (most recent call last):
            ...
            NotImplementedError: Method not implemented for this storage.

        .. versionadded:: 37.1.0

        """

        raise NotImplementedError("Method not implemented for this storage.")

    def restore(self) -> None:
        self.__files__ = {}
        # Restore self.__files__ from content of directory.
        for filename in os.listdir(self.directory):
            if not filename.endswith(".npy"):
                continue
            path = os.path.join(self.directory, filename)
            filename_core = filename.rsplit(".", 1)[0]
            period = periods.period(filename_core)
            self.__files__ = {period: path, **self.__files__}

    def __del__(self) -> None:
        if self.keep:
            return None

        path = pathlib.Path(self.directory)

        if path.exists():
            # Remove the holder temporary files
            shutil.rmtree(self.directory)

        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.directory, os.pardir))

        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)

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

            >>> with tempfile.TemporaryDirectory() as directory:
            ...     storage = DiskRepo(directory)
            ...     storage.put(value, period)
            ...     storage._decode_file(storage.__files__[period])
            EnumArray([<Housing.TENANT: 'Tenant'>])

        """

        enum = self.__enums__.get(file)
        load = numpy.load(file)

        if enum is None:
            return load

        return enums.EnumArray(load, enum)
