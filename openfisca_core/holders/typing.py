# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

from typing import Any
from typing_extensions import Protocol, TypedDict

import abc

import numpy


class Holder(Protocol):
    @abc.abstractmethod
    def clone(self, population: Any) -> Holder: ...

    @abc.abstractmethod
    def get_memory_usage(self) -> Any: ...


class Storage(Protocol):
    @abc.abstractmethod
    def get(self, period: Any) -> Any: ...

    @abc.abstractmethod
    def put(self, values: Any, period: Any) -> None: ...

    @abc.abstractmethod
    def delete(self, period: Any = None) -> None: ...

    def periods(self) -> Any: ...

    @abc.abstractmethod
    def usage(self) -> Any: ...


class MemoryUsage(TypedDict, total=False):
    """Virtual memory usage of a storage."""

    #: The amount of bytes assigned to each value.
    cell_size: float

    #: The :mod:`numpy.dtype` of any, each, and every value.
    dtype: numpy.dtype

    #: The number of arrays for which the storage contains values.
    nb_arrays: int

    #: The number of entities in the current Simulation.
    nb_cells_by_array: int

    #: The number of times the Variable has been computed.
    nb_requests: int

    #: Average times a stored array has been read.
    nb_requests_by_array: int

    #: The total number of bytes used by the storage.
    total_nb_bytes: int
