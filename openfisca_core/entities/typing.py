from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypedDict


class Entity(Protocol):
    ...


class GroupEntity(Protocol):
    ...


class Role(Protocol):
    max: int | None
    subroles: Iterable[Role] | None

    @property
    def key(self) -> str:
        ...


class RoleParams(TypedDict, total=False):
    key: str
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]
