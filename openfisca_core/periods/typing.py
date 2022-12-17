# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

from typing import Any, TypeVar
from typing_extensions import Protocol

A = TypeVar("A", covariant = True)
P = TypeVar("P")


class Add(Protocol[A]):
    def __call__(self, years: int, months: int, week: int, days: int) -> A: ...


class Plural(Protocol[P]):
    def __call__(self, __arg1: P, __arg2: Any = None) -> P: ...


# from typing import Any, Iterable, Iterator, TypeVar
# from typing_extensions import Protocol
#
# import abc
#
# from pendulum.datetime import Date
#
# T = TypeVar("T")
#
#
# class Instant(Protocol[~T]):
#     def __init__(cls, *args: Iterable[int]) -> None: ...
#
#     @abc.abstractmethod
#     def __iter__(self) -> Iterator[int]: ...
#
#     @abc.abstractmethod
#     def __ge__(self, other: T) -> bool: ...
#
#     @abc.abstractmethod
#     def __le__(self, other: T) -> bool: ...
#
#     @abc.abstractmethod
#     def date(self) -> Date: ...
#
#     @abc.abstractmethod
#     def offset(self, offset: str | int, unit: int) -> T: ...
#
#
# class Period(Protocol):
#     @abc.abstractmethod
#     def __iter__(self) -> Any: ...
#
#     @property
#     @abc.abstractmethod
#     def unit(self) -> int: ...
#
#     @property
#     @abc.abstractmethod
#     def start(self) -> T: ...
#
#     # @property
#     # @abc.abstractmethod
#     # def stop(self) -> Instant: ...
#
#     # @abc.abstractmethod
#     # def offset(self, offset: str | int, unit: int | None = None) -> Period: ...
