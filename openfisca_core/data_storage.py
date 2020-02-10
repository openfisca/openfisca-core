import abc
import os
import shutil
from typing import Any, Dict, KeysView, Optional

import numpy

from openfisca_core import periods
from openfisca_core.indexed_enums import EnumArray
from openfisca_core.periods import Period

StateType = Dict[Period, Any]


class StorageLike(abc.ABC):
    """Blueprint for an explicit Storage API."""
    @abc.abstractmethod
    def get(self, state: StateType, key: Period) -> Any:
        ...

    @abc.abstractmethod
    def put(self, state: StateType, key: Period, value: Any) -> StateType:
        ...

    @abc.abstractmethod
    def delete(self, state: StateType, key: Period) -> StateType:
        ...

    @abc.abstractmethod
    def delete_all(self, state: StateType) -> dict:
        ...


class CachingLike(abc.ABC):
    """Blueprint for an explicit Cache API."""

    @abc.abstractmethod
    def get(self, period: Period) -> Any:
        ...

    @abc.abstractmethod
    def put(self, value: Any, period: Period) -> None:
        ...

    @abc.abstractmethod
    def delete(self, period: Optional[Period] = None) -> None:
        ...

    @abc.abstractmethod
    def get_known_periods(self) -> KeysView[Period]:
        ...

    @abc.abstractmethod
    def get_memory_usage(self) -> Dict[str, int]:
        ...


class SupportsPeriodCasting(abc.ABC):
    """
    Extracting eternal period resolution.

    TODO: get rid of.
    """

    def cast_period(self, period: Optional[Period], eternal: bool) -> Period:
        if eternal:
            return periods.period(periods.ETERNITY)

        return periods.period(period)


class MemoryStorage(StorageLike):
    """Responsible for storing and retrieving values in memory."""

    def get(self, state: Dict[Period, Any], key: Period) -> Any:
        return state.get(key)

    def put(self, state: StateType, key: Period, value: Any) -> StateType:
        state[key] = value
        return state

    def delete(self, state: StateType, key: Period) -> StateType:
        return {item: value for item, value in state.items() if not key.contains(item)}

    def delete_all(self, state: StateType) -> dict:
        state.clear()
        return state


class DiskStorage(StorageLike):
    """Responsible for storing and retrieving values on disk."""
    directory: str
    preserve: bool

    def __init__(self, directory: str, preserve: bool) -> None:
        self.directory = directory
        self.preserve = preserve

    def get(self, state: Dict[Period, Any], key: Period) -> Any:
        file = state.get(key)

        if file is None:
            return None

        filepath, value = file

        if value is None:
            return numpy.load(filepath)

        return EnumArray(numpy.load(filepath), value)

    def put(self, state: StateType, key: Period, value: Any) -> StateType:
        filename = str(key)
        filepath = os.path.join(self.directory, filename) + ".npy"

        if isinstance(value, EnumArray):
            state[key] = filepath, value.possible_values
            value = value.view(numpy.ndarray)

        else:
            state[key] = filepath, None

        numpy.save(filepath, value)

        return state

    def delete(self, state: StateType, key: Period) -> StateType:
        return {item: value for item, value in state.items() if not key.contains(item)}

    def delete_all(self, state: StateType) -> dict:
        state.clear()
        return state

    def restore(self, state: StateType) -> StateType:
        state = self.delete_all(state)

        # Restore files from content of directory.
        for filename in os.listdir(self.directory):
            if not filename.endswith('.npy'):
                continue

            filepath = os.path.join(self.directory, filename)
            filename_core = filename.rsplit('.', 1)[0]
            period = periods.period(filename_core)
            state[period] = filepath, None

        return state

    def __del__(self) -> None:
        if self.preserve:
            return

        # Remove the holder temporary files
        shutil.rmtree(self.directory)

        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.directory, os.pardir))

        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)


class InMemoryStorage(CachingLike, SupportsPeriodCasting):
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory.

    TODO: separate concerns between the caching API and the storing API.
    """

    _arrays: dict
    is_eternal: bool
    storage: MemoryStorage

    def __init__(self, is_eternal: bool = False) -> None:
        self._arrays = {}
        self.is_eternal = is_eternal
        self.storage = MemoryStorage()

    def get(self, period: Period) -> Any:
        casted: Period = self.cast_period(period, self.is_eternal)
        return self.storage.get(self._arrays, casted)

    def put(self, value: Any, period: Period) -> None:
        casted: Period = self.cast_period(period, self.is_eternal)
        self._arrays = self.storage.put(self._arrays, casted, value)

    def delete(self, period: Optional[Period] = None) -> None:
        if period is None:
            self._arrays = self.storage.delete_all(self._arrays)
            return

        casted: Period = self.cast_period(period, self.is_eternal)
        self._arrays = self.storage.delete(self._arrays, casted)

    # TODO: decide what to do with this.
    def get_known_periods(self) -> KeysView[Period]:
        return self._arrays.keys()

    # TODO: decide what to do with this.
    def get_memory_usage(self) -> Dict[str, int]:
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


class OnDiskStorage(CachingLike, SupportsPeriodCasting):
    """
    Low-level class responsible for storing and retrieving calculated vectors on disk.

    TODO: separate concerns between the caching API and the storing API.
    """

    _files: dict
    is_eternal: bool
    storage: DiskStorage

    def __init__(
            self,
            storage_dir: str,
            is_eternal: bool = False,
            preserve_storage_dir: bool = False,
            ) -> None:
        self._files = {}
        self.is_eternal = is_eternal
        self.storage = DiskStorage(storage_dir, preserve_storage_dir)

    def get(self, period: Period) -> Any:
        casted: Period = self.cast_period(period, self.is_eternal)
        return self.storage.get(self._files, casted)

    def put(self, value: Any, period: Period) -> None:
        casted: Period = self.cast_period(period, self.is_eternal)
        self._files = self.storage.put(self._files, casted, value)

    def delete(self, period: Optional[Period] = None) -> None:
        if period is None:
            self._files = self.storage.delete_all(self._files)
            return

        casted: Period = self.cast_period(period, self.is_eternal)
        self._files = self.storage.delete(self._files, casted)

    # TODO: decide what to do with this.
    def get_known_periods(self) -> KeysView[Period]:
        return self._files.keys()

    # TODO: decide what to do with this.
    def get_memory_usage(self) -> Dict[str, int]:
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

    #  TODO: remove this method.
    def _decode_file(self, file):
        enum = self._enums.get(file)
        if enum is not None:
            return EnumArray(numpy.load(file), enum)
        else:
            return numpy.load(file)
