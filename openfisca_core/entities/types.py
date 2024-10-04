from typing_extensions import Required, TypedDict

from openfisca_core.types import (
    CoreEntity,
    EntityKey,
    EntityPlural,
    GroupEntity,
    Role,
    RoleKey,
    RolePlural,
    SingleEntity,
    TaxBenefitSystem,
    Variable,
    VariableName,
)

# Entities


class RoleParams(TypedDict, total=False):
    key: Required[str]
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]


__all__ = [
    "CoreEntity",
    "EntityKey",
    "EntityPlural",
    "GroupEntity",
    "Role",
    "RoleKey",
    "RoleParams",
    "RolePlural",
    "SingleEntity",
    "TaxBenefitSystem",
    "Variable",
    "VariableName",
]
