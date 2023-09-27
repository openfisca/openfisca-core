from abc import abstractmethod
from typing import Protocol


class Entity(Protocol):
    ...


class GroupEntity(Protocol):
    ...


class Role(Protocol):
    @property
    @abstractmethod
    def key(self) -> str:
        ...
