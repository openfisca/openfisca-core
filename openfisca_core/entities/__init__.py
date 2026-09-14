"""Provide a way of representing the entities of a rule system."""

from . import types
from .entity import Entity
from .helpers import build_entity, find_role
from .role import Role

check_role_validity = Entity.check_role_validity

__all__ = [
    "Entity",
    "Role",
    "build_entity",
    "check_role_validity",
    "find_role",
    "types",
]
