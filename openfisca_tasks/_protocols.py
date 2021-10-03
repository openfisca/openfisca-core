from __future__ import annotations

import abc
from typing import Any, Generator, Sequence

from typing_extensions import Protocol


class HasExit(Protocol):
    exit: int

    @abc.abstractmethod
    def __call__(self, __progress: SupportsProgress) -> None:
        ...


class SupportsParsing(Protocol):

    contracts: Sequence[Any]

    @abc.abstractmethod
    def __enter__(self) -> Generator:
        ...

    @abc.abstractmethod
    def __exit__(self, *__: Any) -> None:
        ...

    @abc.abstractmethod
    def parse(self, __file: str) -> None:
        ...


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
    def next(self) -> None:
        ...

    @abc.abstractmethod
    def wipe(self) -> None:
        ...
