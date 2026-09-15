from __future__ import annotations

from collections.abc import Iterable, Sequence

from . import types as t
from .entity import Entity

def find_role(
    entity: Entity,
    key: t.RoleKey,
    *,
    total: None | int = None,
) -> None | t.Role:
    """Find a ``Role`` in a ``Entity``.

    Args:
        roles: The roles to search.
        key: The key of the role to find.
        total: The ``max`` attribute of the role to find.

    Returns:
        Role: The role if found
        None: Else ``None``.

    Examples:
        >>> person_entity = Entity("person", "persons", "Person", "An individual")

        >>> principal = t.RoleParams(
        ...     key="principal",
        ...     label="Principal",
        ...     doc="Person focus of a calculation in a family context.",
        ...     max=1,
        ... )

        >>> partner = t.RoleParams(
        ...     key="partner",
        ...     plural="partners",
        ...     label="Partners",
        ...     doc="Persons partners of the principal.",
        ... )

        >>> parent = t.RoleParams(
        ...     key="parent",
        ...     plural="parents",
        ...     label="Parents",
        ...     doc="Persons parents of children of the principal",
        ...     subroles=["first_parent", "second_parent"],
        ... )

        >>> group_entity = Entity(
        ...     key="family",
        ...     plural="families",
        ...     label="Family",
        ...     doc="A Family represents a collection of related persons.",
        ... )

        >>> group_entity.add_relationship(
        ...     person_entity,
        ...     [principal, partner, parent],
        ... )

        >>> find_role(group_entity, "principal", total=1)
        Role(principal)

        >>> find_role(group_entity, "partner")
        Role(partner)

        >>> find_role(group_entity, "parent", total=2)
        Role(parent)

        >>> find_role(group_entity, "first_parent", total=1)
        Role(first_parent)

    """
    for relationship in entity.relationships:
        if relationship.b == entity:
            continue
        for role in relationship.roles:
            if role.subroles:
                for subrole in role.subroles:
                    if (subrole.max == total) and (subrole.key == key):
                        return subrole

            if (role.max == total) and (role.key == key):
                return role

    return None


__all__ = ["find_role"]
