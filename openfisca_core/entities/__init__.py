"""Provide a way of representing the entities of a rule system."""

from . import types
from ._core_entity import CoreEntity
from ._errors import TaxBenefitSystemUnsetError, VariableNotFoundError
from .entity import Entity
from .group_entity import GroupEntity
from .helpers import build_entity, find_role
from .role import Role

SingleEntity = Entity

__all__ = [
    "CoreEntity",
    "Entity",
    "GroupEntity",
    "Role",
    "SingleEntity",
    "TaxBenefitSystemUnsetError",
    "VariableNotFoundError",
    "build_entity",
    "find_role",
    "types",
]
