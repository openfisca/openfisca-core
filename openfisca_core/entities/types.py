from typing_extensions import Required, TypedDict

from openfisca_core.types import (
    Entity,
    EntityKey,
    EntityPlural,
    Role,
    RoleKey,
    RolePlural,
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
    "Entity",
    "EntityKey",
    "EntityPlural",
    "Role",
    "RoleKey",
    "RoleParams",
    "RolePlural",
    "TaxBenefitSystem",
    "Variable",
    "VariableName",
]
