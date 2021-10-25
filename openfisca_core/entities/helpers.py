from __future__ import annotations

from typing import Any, Optional, Sequence
from openfisca_core.typing import EntityProtocol, RoleSchema

from .entity import Entity
from .group_entity import GroupEntity
from .role import Role


def build_entity(
        key: str,
        plural: str,
        label: str,
        doc: str = "",
        roles: Optional[Sequence[RoleSchema]] = None,
        is_person: bool = False,
        class_override: Optional[Any] = None,
        containing_entities: Sequence[str] = (),
        ) -> EntityProtocol:
    """Builds an :class:`.Entity` or a :class:`.GroupEntity`.

    Args:
        key: Key to identify the :class:`.Entity` or :class:`.GroupEntity`.
        plural: ``key``, pluralised.
        label: A summary description.
        doc: A full description.
        roles: A list of :class:`.Role`, if it's a :class:`.GroupEntity`.
        is_person: If is an individual, or not.
        class_override: ?
        containing_entities: Keys of contained entities.

    Returns:
        :obj:`.Entity` or :obj:`.GroupEntity`:
        :obj:`.Entity`: When ``is_person`` is True.
        :obj:`.GroupEntity`: When ``is_person`` is False.

    Raises:
        ValueError: If ``roles`` is not iterable.

    Examples:
        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles = [],
        ...     containing_entities = (),
        ...     )
        GroupEntity(syndicate)

        >>> build_entity(
        ...     "company",
        ...     "companies",
        ...     "A small or medium company.",
        ...     is_person = True,
        ...     )
        Entity(company)

        >>> role = Role({"key": "key"}, object())
        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles = role,
        ...     )
        Traceback (most recent call last):
        ValueError: Invalid value 'key' for 'roles', must be a list.

    .. versionchanged:: 35.8.0
        Instead of raising :exc:`TypeError` when ``roles`` is None, it does
        now raise :exc:`ValueError` when ``roles`` is not iterable.

    .. versionchanged:: 35.7.0
        Builder accepts a ``containing_entities`` attribute, that allows the
        defining of group entities which entirely contain other group entities.

    """

    if is_person:
        return Entity(key, plural, label, doc)

    if isinstance(roles, (list, tuple)):
        return GroupEntity(key, plural, label, doc, roles, containing_entities)

    raise ValueError(f"Invalid value '{roles}' for 'roles', must be a list.")


def check_role_validity(role: Any) -> None:
    """Checks if ``role`` is an instance of :class:`.Role`.

    Args:
        role: Any object.

    Raises:
        ValueError: When ``role`` is not a :class:`.Role`.

    Examples:
        >>> role = Role({"key": "key"}, object())
        >>> check_role_validity(role)

        >>> check_role_validity("hey!")
        Traceback (most recent call last):
        ValueError: hey! is not a valid role

    .. versionadded:: 35.8.0

    """

    if role is not None and not isinstance(role, Role):
        raise ValueError(f"{role} is not a valid role")
