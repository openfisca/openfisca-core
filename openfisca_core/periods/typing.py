# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import typing_extensions
from typing import Any, Iterable, Iterator
from typing_extensions import Protocol

import abc

from pendulum.datetime import Date


@typing_extensions.runtime_checkable
class Instant(Protocol):
    def __init__(cls, *args: Iterable[int]) -> None: ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[int]: ...

    @abc.abstractmethod
    def __ge__(self, other: object) -> bool: ...

    @abc.abstractmethod
    def __le__(self, other: object) -> bool: ...

    @abc.abstractmethod
    def date(self) -> Date: ...

    @abc.abstractmethod
    def offset(self, offset: str | int, unit: int) -> Instant: ...


@typing_extensions.runtime_checkable
class Period(Protocol):
    @abc.abstractmethod
    def __iter__(self) -> Any: ...

    @property
    @abc.abstractmethod
    def unit(self) -> int: ...

    @property
    @abc.abstractmethod
    def start(self) -> Instant: ...

    @property
    @abc.abstractmethod
    def stop(self) -> Instant: ...

    @abc.abstractmethod
    def offset(self, offset: str | int, unit: int | None = None) -> Period: ...
