from __future__ import annotations

from typing import Protocol, TypedDict


class Entity(Protocol):
    ...


class GroupEntity(Protocol):
    ...


class Role(Protocol):
    ...


class RoleParams(TypedDict, total=False):
    key: str
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]
