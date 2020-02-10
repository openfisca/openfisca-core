import abc
import os
import shutil
from typing import Any, Dict, List, Union

import numpy

from openfisca_core import indexed_enums
from openfisca_core import periods

from typing_extensions import Protocol


class SupportsCaching(Protocol):

    @abc.abstractmethod
    def get(self, period: periods.Period) -> Any:
        ...

    @abc.abstractmethod
    def put(self, value: Any, period: periods.Period) -> None:
        ...

    @abc.abstractmethod
    def delete(self, period: periods.Period) -> None:
        ...

    @abc.abstractmethod
    def delete_all(self) -> None:
        ...


class SupportsKnownPeriods(Protocol):

    @abc.abstractmethod
    def known_periods(self) -> List[periods.Period]:
        ...


class SupportsMemoryUsage(Protocol):

    @abc.abstractmethod
    def memory_usage(self) -> Dict[str, int]:
        ...


class SupportsPeriod(Protocol):

    @abc.abstractmethod
    def period(self, period: periods.Period) -> periods.Period:
        ...


class ExactCaching(SupportsPeriod):

    def period(self, period: periods.Period) -> periods.Period:
        return periods.period(period)


class EternalCaching(SupportsPeriod):

    def period(self, period: periods.Period) -> periods.Period:
        return periods.period(periods.ETERNITY)


class MemoryCaching(SupportsCaching, SupportsKnownPeriods, SupportsMemoryUsage):
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory.
    """

    _arrays: dict

    def __init__(self) -> None:
        self._arrays = {}

    def get(self, period: periods.Period) -> Any:
        values = self._arrays.get(period)

        if values is None:
            return None

        return values

    def put(self, value: Any, period: periods.Period) -> None:
        self._arrays[period] = value

    def delete(self, period: periods.Period) -> None:
        self._arrays = self._pop(period, list(self._arrays.items()))

    def delete_all(self) -> None:
        self._arrays = {}

    def known_periods(self) -> List[periods.Period]:
        return list(self._arrays.keys())

    def memory_usage(self) -> Dict[str, int]:
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

    def _pop(self, period: periods.Period, items: list) -> dict:
        return {item: value for item, value in items if not period.contains(item)}


class PersistentCaching(SupportsCaching, SupportsKnownPeriods, SupportsMemoryUsage):
    """
    Low-level class responsible for storing and retrieving calculated vectors on disk.
    """

    _files: dict
    _enums: dict
    storage_dir: str
    preserve_storage_dir: bool

    def __init__(self, storage_dir: str, preserve_storage_dir: bool = False) -> None:
        self._files = {}
        self._enums = {}
        self.storage_dir = storage_dir
        self.preserve_storage_dir = preserve_storage_dir

    def get(self, period: periods.Period) -> Any:
        values = self._files.get(period)

        if values is None:
            return None

        return self._decode_file(values)

    def put(self, value: Any, period: periods.Period) -> None:
        filename = str(period)
        path = os.path.join(self.storage_dir, filename) + '.npy'

        if isinstance(value, indexed_enums.EnumArray):
            self._enums[path] = value.possible_values
            value = value.view(numpy.ndarray)

        numpy.save(path, value)
        self._files[period] = path

    def delete(self, period: periods.Period) -> None:
        self._files = self._pop(period, list(self._files.items()))

    def delete_all(self) -> None:
        self._files = {}

    def known_periods(self) -> List[periods.Period]:
        return list(self._files.keys())

    def memory_usage(self) -> Dict[str, int]:
        if not self._files:
            return {
                "nb_files": 0,
                "total_nb_bytes": 0,
                "cell_size": numpy.nan,
                }

        nb_files = len(self._files)
        file = next(iter(self._files.values()))
        size = os.path.getsize(file)
        array = self._decode_file(file)

        return {
            "nb_files": nb_files,
            "total_nb_bytes": size * nb_files,
            "cell_size": array.itemsize,
            }

    def restore(self):
        self._files = files = {}
        # Restore self._files from content of storage_dir.
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.npy'):
                continue
            path = os.path.join(self.storage_dir, filename)
            filename_core = filename.rsplit('.', 1)[0]
            period = periods.period(filename_core)
            files[period] = path

    def _pop(self, period: periods.Period, items: list) -> dict:
        return {item: value for item, value in items if not period.contains(item)}

    def _decode_file(self, file):
        enum = self._enums.get(file)
        if enum is not None:
            return indexed_enums.EnumArray(numpy.load(file), enum)
        else:
            return numpy.load(file)

    def __del__(self):
        if self.preserve_storage_dir:
            return
        shutil.rmtree(self.storage_dir)  # Remove the holder temporary files
        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.storage_dir, os.pardir))
        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)


class Cache(SupportsCaching):

    TimeType = Union[ExactCaching, EternalCaching]
    StoreType = Union[MemoryCaching, PersistentCaching]

    timeness: TimeType
    storage: StoreType

    def __init__(self, timeness: TimeType, storage: StoreType) -> None:
        self.timeness = timeness
        self.storage = storage

    def get(self, period: periods.Period) -> Any:
        period = self.timeness.period(period)
        return self.storage.get(period)

    def put(self, value: Any, period: periods.Period) -> None:
        period = self.timeness.period(period)
        self.storage.put(value, period)

    def delete(self, period: periods.Period) -> None:
        period = self.timeness.period(period)
        self.storage.delete(period)

    def delete_all(self) -> None:
        self.storage.delete_all()
