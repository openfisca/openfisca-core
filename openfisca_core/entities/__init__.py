"""Provide a way of representing the entities of a rule system."""

from . import types
from ._core_entity import CoreEntity
from .entity import Entity
from .group_entity import GroupEntity
from .helpers import build_entity, find_role
from .role import Role

SingleEntity = Entity
check_role_validity = CoreEntity.check_role_validity

__all__ = [
    "CoreEntity",
    "Entity",
    "GroupEntity",
    "Role",
    "SingleEntity",
    "build_entity",
    "check_role_validity",
    "find_role",
    "types",
]
