from __future__ import annotations

import abc

from typing_extensions import Literal, Protocol

What = Literal["this", "that"]


class HasIndex(Protocol):
    index: int


class HasExit(Protocol):
    exit: HasIndex

    @abc.abstractmethod
    def __call__(self) -> None:
        ...
