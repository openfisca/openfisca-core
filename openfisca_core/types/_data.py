"""Data-model.

The data-model is composed of structures meant to hold data in a certain way.
Their identity is equivalent to the sum of their properties. If two data
objects hold the same data, they are for all purposes equal and fungible.

Examples:
    >>> from openfisca_core import periods

    >>> this = periods.Instant((1234, 5, 6))
    >>> that = periods.Instant((1234, 5, 6))
    >>> this == that
    True

    >>> that = periods.Instant((1234, 7, 8))
    >>> this == that
    False


"""

from __future__ import annotations

import typing_extensions
from typing import Any, Sequence, TypeVar, Union
from typing_extensions import Protocol, TypedDict

import abc

import numpy
from nptyping import types, NDArray as Array

T = TypeVar("T", bool, bytes, float, int, object, str)

types._ndarray_meta._Type = Union[type, numpy.dtype, TypeVar]

ArrayLike = Union[Array[T], Sequence[T]]
""":obj:`typing.Generic`: Type of any castable to :class:`numpy.ndarray`.

These include any :obj:`numpy.ndarray` and sequences (like
:obj:`list`, :obj:`tuple`, and so on).

Examples:
    >>> ArrayLike[float]
    typing.Union[numpy.ndarray, typing.Sequence[float]]

    >>> ArrayLike[str]
    typing.Union[numpy.ndarray, typing.Sequence[str]]

Note:
    It is possible since numpy version 1.21 to specify the type of an
    array, thanks to `numpy.typing.NDArray`_::

        from numpy.typing import NDArray
        NDArray[numpy.float64]

    `mypy`_ provides `duck type compatibility`_, so an :obj:`int` is
    considered to be valid whenever a :obj:`float` is expected.

Todo:
    * Refactor once numpy version >= 1.21 is used.

.. versionadded:: 35.5.0

.. versionchanged:: 35.6.0
    Moved to :mod:`.types`

.. _mypy:
    https://mypy.readthedocs.io/en/stable/

.. _duck type compatibility:
    https://mypy.readthedocs.io/en/stable/duck_type_compatibility.html

.. _numpy.typing.NDArray:
    https://numpy.org/doc/stable/reference/typing.html#numpy.typing.NDArray

"""


class Enum(Protocol):
    """Enum protocol."""


class EnumArray(Protocol):
    """EnumArray protocol."""


class Instant(Protocol):
    """Instant protocol."""


class MemoryUsage(TypedDict, total = False):
    """Virtual memory usage of a Holder.

    Attributes:
        cell_size: The amount of bytes assigned to each value.
        dtype: The :mod:`numpy.dtype` of any, each, and every value.
        nb_arrays: The number of periods for which the Holder contains values.
        nb_cells_by_array: The number of entities in the current Simulation.
        nb_requests: The number of times the Variable has been computed.
        nb_requests_by_array: Average times a stored array has been read.
        total_nb_bytes: The total number of bytes used by the Holder.

    """

    cell_size: float
    dtype: numpy.dtype[Any]
    nb_arrays: int
    nb_cells_by_array: int
    nb_requests: int
    nb_requests_by_array: int
    total_nb_bytes: int


@typing_extensions.runtime_checkable
class Period(Protocol):
    """Period protocol."""

    @property
    @abc.abstractmethod
    def start(self) -> Any:
        """Abstract method."""
    @property
    @abc.abstractmethod
    def unit(self) -> Any:
        """Abstract method."""

    @abc.abstractmethod
    def contains(self, other: object) -> bool:
        """Abstract method."""
