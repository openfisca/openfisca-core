# pylint: disable=missing-class-docstring, missing-function-docstring

from __future__ import annotations

from typing import Any, Tuple, TypeVar
from typing_extensions import Protocol

import abc

from pendulum.datetime import Date

Self = TypeVar("Self")
T = TypeVar("T", covariant = True)
U = TypeVar("U", covariant = True)
V = TypeVar("V", covariant = True)


class Offsetable(Protocol[T, U, V]):
    @abc.abstractmethod
    def __init__(self, values: Tuple[T, U, V]) -> None:
        ...

    @abc.abstractmethod
    def __le__(self, other: Any) -> bool:
        ...

    @abc.abstractmethod
    def __ge__(self, other: Any) -> bool:
        ...

    @property
    @abc.abstractmethod
    def year(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def month(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def day(self) -> int:
        ...

    @abc.abstractmethod
    def add(self, unit: str, count: int) -> Date:
        ...

    @abc.abstractmethod
    def date(self) -> Date:
        ...

    @abc.abstractmethod
    def offset(self: Self, offset: Any, unit: Any) -> Self:
        ...
