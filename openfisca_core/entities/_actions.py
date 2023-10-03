"""Actions related to the entities context."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .entity import Entity
from .group_entity import GroupEntity


def build_entity(
    key: str,
    plural: str,
    label: str,
    doc: str = "",
    roles: Iterable[Mapping[str, Any]] | None = None,
    is_person: bool = False,
    class_override: Any | None = None,
    containing_entities: Iterable[str] = (),
) -> Entity | GroupEntity:
    """Build an Entity` or GroupEntity.

    Args:
        key (str): Key to identify the Entity or GroupEntity.
        plural (str): ``key``, pluralised.
        label (str): A summary description.
        doc (str): A full description.
        roles (list) : A list of Role, if it's a GroupEntity.
        is_person (bool): If is an individual, or not.
        class_override: ?
        containing_entities (list): Keys of contained entities.

    Returns:
        Entity or GroupEntity:
        Entity: When ``is_person`` is True.
        GroupEntity: When ``is_person`` is False.

    Raises:
        ValueError: If ``roles`` is not an Iterable.

    Examples:
        >>> from openfisca_core import entities

        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles = [],
        ...     containing_entities = [],
        ...     )
        GroupEntity(syndicate)

        >>> build_entity(
        ...     "company",
        ...     "companies",
        ...     "A small or medium company.",
        ...     is_person = True,
        ...     )
        Entity(company)

        >>> role = entities.Role({"key": "key"}, object())

        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles = role,
        ...     )
        Traceback (most recent call last):
        ValueError: Invalid value 'key' for 'roles', must be an iterable.

    """

    if is_person:
        return Entity(key, plural, label, doc)

    if isinstance(roles, (list, tuple)):
        return GroupEntity(key, plural, label, doc, roles, containing_entities)

    raise ValueError(f"Invalid value '{roles}' for 'roles', must be an iterable.")
