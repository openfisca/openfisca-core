from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol
from typing_extensions import TypedDict

from openfisca_core import types as t

# Entities


class CoreEntity(t.CoreEntity, Protocol):
    ...


class SingleEntity(t.SingleEntity, Protocol):
    key: str
    plural: str | None


class GroupEntity(t.GroupEntity, Protocol):
    ...


class Role(t.Role, Protocol):
    subroles: Iterable[Role] | None


class RoleParams(TypedDict, total=False):
    key: str
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]
