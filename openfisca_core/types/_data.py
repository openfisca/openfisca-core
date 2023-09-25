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

import abc
import typing_extensions
from numpy.typing import NDArray as Array  # noqa: F401
from typing import Any, TypeVar
from typing_extensions import Protocol

T = TypeVar("T", bool, bytes, float, int, object, str)


class Enum(Protocol):
    """Enum protocol."""


class EnumArray(Protocol):
    """EnumArray protocol."""


class Instant(Protocol):
    """Instant protocol."""


@typing_extensions.runtime_checkable
class Period(Protocol):
    """Period protocol."""

    @property
    @abc.abstractmethod
    def size(self) -> int:
        """Abstract property."""

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
