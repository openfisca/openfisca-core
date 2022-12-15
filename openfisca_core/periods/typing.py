# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import typing_extensions
from typing import Any
from typing_extensions import Protocol

import abc


@typing_extensions.runtime_checkable
class Instant(Protocol):
    @property
    @abc.abstractmethod
    def date(self) -> Any: ...

    @abc.abstractmethod
    def offset(self, offset: Any, unit: Any) -> Any: ...


@typing_extensions.runtime_checkable
class Period(Protocol):
    @abc.abstractmethod
    def __iter__(self) -> Any: ...

    @property
    @abc.abstractmethod
    def unit(self) -> Any: ...

    @property
    @abc.abstractmethod
    def start(self) -> Any: ...

    @property
    @abc.abstractmethod
    def stop(self) -> Any: ...

    @abc.abstractmethod
    def offset(self, offset: Any, unit: Any = None) -> Any: ...
