from __future__ import annotations

from abc import abstractmethod
from typing import Protocol


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
