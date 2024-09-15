from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypedDict

from openfisca_core import types

# Entities


class CoreEntity(types.CoreEntity, Protocol):
    ...


class SingleEntity(types.SingleEntity, Protocol):
    key: str
    plural: str | None


class GroupEntity(types.GroupEntity, Protocol):
    ...


class Role(types.Role, Protocol):
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
