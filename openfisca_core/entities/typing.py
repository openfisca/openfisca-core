from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol, TypedDict


class DescriptionParams(TypedDict, total=False):
    key: str
    plural: str | None
    label: str | None
    doc: str | None
    subroles: Sequence[str] | None


class Entity(Protocol):
    @property
    @abstractmethod
    def key(self) -> str:
        ...


class GroupEntity(Protocol):
    ...


class Role(Protocol):
    @property
    @abstractmethod
    def entity(self) -> Entity | GroupEntity:
        ...

    @property
    @abstractmethod
    def key(self) -> str:
        ...


class SubRole(Protocol):
    ...
