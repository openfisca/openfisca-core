from __future__ import annotations

from collections.abc import Iterable, Sequence

from . import types as t
from .entity import Entity as SingleEntity
from .group_entity import GroupEntity


def build_entity(
    key: str,
    plural: str,
    label: str,
    doc: str = "",
    roles: None | Sequence[t.RoleParams] = None,
    is_person: bool = False,
    class_override: object = None,
    containing_entities: Sequence[str] = (),
) -> t.SingleEntity | t.GroupEntity:
    """Build a SingleEntity or a GroupEntity.

    Args:
        key: Key to identify the :class:`.Entity`. or :class:`.GroupEntity`.
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
        NotImplementedError: if ``roles`` is None.

    Examples:
        >>> from openfisca_core import entities

        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles=[],
        ...     containing_entities=(),
        ... )
        GroupEntity(syndicate)

        >>> build_entity(
        ...     "company",
        ...     "companies",
        ...     "A small or medium company.",
        ...     is_person=True,
        ... )
        Entity(company)

        >>> role = entities.Role({"key": "key"}, object())

        >>> build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ...     roles=role,
        ... )
        Traceback (most recent call last):
        TypeError: 'Role' object is not iterable

    """

    if is_person:
        return SingleEntity(key, plural, label, doc)

    if roles is not None:
        return GroupEntity(
            key,
            plural,
            label,
            doc,
            roles,
            containing_entities=containing_entities,
        )

    raise NotImplementedError


def find_role(
    roles: Iterable[t.Role],
    key: t.RoleKey,
    *,
    total: None | int = None,
) -> None | t.Role:
    """Find a Role in a GroupEntity.

    Args:
        roles (Iterable[Role]): The roles to search.
        key (str): The key of the role to find. Defaults to `None`.
        total (int | None): The `max` attribute of the role to find.

    Returns:
        Role | None: The role if found, else `None`.

    Examples:
        >>> from openfisca_core.entities.types import RoleParams

        >>> principal = RoleParams(
        ...     key="principal",
        ...     label="Principal",
        ...     doc="Person focus of a calculation in a family context.",
        ...     max=1,
        ... )

        >>> partner = RoleParams(
        ...     key="partner",
        ...     plural="partners",
        ...     label="Partners",
        ...     doc="Persons partners of the principal.",
        ... )

        >>> parent = RoleParams(
        ...     key="parent",
        ...     plural="parents",
        ...     label="Parents",
        ...     doc="Persons parents of children of the principal",
        ...     subroles=["first_parent", "second_parent"],
        ... )

        >>> group_entity = build_entity(
        ...     key="family",
        ...     plural="families",
        ...     label="Family",
        ...     doc="A Family represents a collection of related persons.",
        ...     roles=[principal, partner, parent],
        ... )

        >>> find_role(group_entity.roles, "principal", total=1)
        Role(principal)

        >>> find_role(group_entity.roles, "partner")
        Role(partner)

        >>> find_role(group_entity.roles, "parent", total=2)
        Role(parent)

        >>> find_role(group_entity.roles, "first_parent", total=1)
        Role(first_parent)

    """
    for role in roles:
        if role.subroles:
            for subrole in role.subroles:
                if (subrole.max == total) and (subrole.key == key):
                    return subrole

        if (role.max == total) and (role.key == key):
            return role

    return None


__all__ = ["build_entity", "find_role"]
