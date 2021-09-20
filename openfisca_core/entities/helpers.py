from typing import Any, Iterable, Optional

from openfisca_core.types import Personifiable, Rolifiable, RoleLike

from .entity import Entity
from .group_entity import GroupEntity


def build_entity(
        key: str,
        plural: str,
        label: str,
        doc: str = "",
        roles: Optional[Iterable[RoleLike]] = None,
        is_person: bool = False,
        class_override: Optional[Any] = None,
        ) -> Personifiable:
    """Builds an :class:`.Entity` or a :class:`.GroupEntity`.

    Args:
        key: Key to identify the :class:`.Entity` or :class:`.GroupEntity`.
        plural: ``key``, pluralised.
        label: A summary description.
        doc: A full description.
        roles: A list of :class:`.Role`, if it's a :class:`.GroupEntity`.
        is_person: If is an individual, or not.
        class_override: ?

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
        ...     )
        <GroupEntity(syndicate)>

        >>> build_entity(
        ...     "company",
        ...     "companies",
        ...     "A small or medium company.",
        ...     is_person = True,
        ...     )
        <Entity(company)>

    .. versionchanged:: 35.7.0
        Instead of raising :exc:`TypeError` when ``roles`` is None, it does
        now raise :exc:`ValueError` when ``roles`` is not iterable.

    """

    if is_person:
        return Entity(key, plural, label, doc)

    if roles is not None and hasattr(roles, "__iter__"):
        return GroupEntity(key, plural, label, doc, roles)

    raise ValueError(f"Invalid value '{roles}' for 'roles', must be iterable.")


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

    if role is not None and not isinstance(role, Rolifiable):
        raise ValueError(f"{role} is not a valid role")
