# pylint: disable=missing-class-docstring, missing-function-docstring

from __future__ import annotations

from typing import Any, Iterator, TypeVar
from typing_extensions import Protocol

import abc

from pendulum.datetime import Date

_T = TypeVar("_T", covariant = True)
_U = TypeVar("_U", covariant = True)
_V = TypeVar("_V", covariant = True)
_Self = TypeVar("_Self")


class _Offsetable(Protocol[_T, _U, _V]):
    @abc.abstractmethod
    def __init__(self, *args: _T | _U | _V) -> None:
        ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[_T | _U | _V]:
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
    def date(self) -> Date:
        ...

    @abc.abstractmethod
    def offset(self: _Self, offset: Any, unit: Any) -> _Self:
        ...

    @abc.abstractmethod
    def _add(self, unit: str, count: int) -> Date:
        ...


Instant = _Offsetable[int, int, int]

Period = _Offsetable[Any, Instant, int]
