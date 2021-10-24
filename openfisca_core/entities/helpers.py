from __future__ import annotations

from typing import Any

from .role import Role
from .entity import Entity
from .group_entity import GroupEntity


def build_entity(key, plural, label, doc = "", roles = None, is_person = False, containing_entities = (), class_override = None):
    if is_person:
        return Entity(key, plural, label, doc, containing_entities)
    else:
        return GroupEntity(key, plural, label, doc, roles)


def check_role_validity(role: Any) -> None:
    """Checks if ``role`` is an instance of :class:`.Role`.

    Args:
        role: Any object.

    Raises:
        ValueError: When ``role`` is not a :class:`.Role`.

    Examples:
        >>> from openfisca_core.entities import Role
        >>> role = Role({"key": "key"}, object())
        >>> check_role_validity(role)

    .. versionadded:: 35.7.0

    """

    if role is not None and not isinstance(role, Role):
        raise ValueError(f"{role} is not a valid role")
