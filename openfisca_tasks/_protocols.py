from __future__ import annotations

import abc
from typing import Any, Generator, Sequence, Set

from typing_extensions import Protocol


class HasExit(Protocol):

    exit: HasIndex

    @abc.abstractmethod
    def __call__(self) -> None:
        ...


class HasFiles(Protocol):

    changed_files: Sequence[str]

    actual: SupportsParsing
    before: SupportsParsing

    @abc.abstractmethod
    def __init__(self) -> None:
        ...


class HasIndex(Protocol):

    index: int


class SupportsParsing(Protocol):

    contracts: Sequence[Any]
    to_parse: Set[str]
    builder: Any
    repo: Any

    @abc.abstractmethod
    def __enter__(self) -> Generator:
        ...

    @abc.abstractmethod
    def __exit__(self, *__: Any) -> None:
        ...

    @abc.abstractmethod
    def __call__(self, __file: str) -> None:
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
    def then(self) -> None:
        ...

    @abc.abstractmethod
    def wipe(self) -> None:
        ...
