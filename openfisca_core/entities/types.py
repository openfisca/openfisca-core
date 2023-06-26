from __future__ import annotations

from collections.abc import Iterable
from typing import NewType, Protocol
from typing_extensions import Required, TypedDict

from openfisca_core import types as t

# Entities

#: For example "person".
EntityKey = NewType("EntityKey", str)

#: For example "persons".
EntityPlural = NewType("EntityPlural", str)

#: For example "principal".
RoleKey = NewType("RoleKey", str)

#: For example "parents".
RolePlural = NewType("RolePlural", str)


class CoreEntity(t.CoreEntity, Protocol):
    key: EntityKey
    plural: EntityPlural | None


class SingleEntity(t.SingleEntity, Protocol): ...


class GroupEntity(t.GroupEntity, Protocol): ...


class Role(t.Role, Protocol):
    subroles: Iterable[Role] | None


class RoleParams(TypedDict, total=False):
    key: Required[str]
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]


# Tax-Benefit systems


class TaxBenefitSystem(t.TaxBenefitSystem, Protocol): ...


# Variables


class Variable(t.Variable, Protocol): ...
