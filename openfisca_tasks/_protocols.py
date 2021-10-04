from __future__ import annotations

import abc

from typing_extensions import Protocol


class HasExit(Protocol):

    exit: HasIndex

    @abc.abstractmethod
    def __call__(self) -> None:
        ...


class HasIndex(Protocol):

    index: int


class SupportsProgress(Protocol):

    @abc.abstractmethod
    def init(self) -> None:
        ...

    @abc.abstractmethod
    def push(self, __count: int, __total: int) -> None:
        ...

    @abc.abstractmethod
    def okay(self, __message: str) -> None:
        ...

    @abc.abstractmethod
    def info(self, __message: str) -> None:
        ...

    @abc.abstractmethod
    def warn(self, __message: str) -> None:
        ...

    @abc.abstractmethod
    def fail(self) -> None:
        ...

    @abc.abstractmethod
    def then(self) -> None:
        ...

    @abc.abstractmethod
    def wipe(self) -> None:
        ...
