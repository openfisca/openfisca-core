from __future__ import annotations

from collections.abc import Iterable, Sequence

from . import types as t
from .entity import Entity

def build_entity(
    key: str,
    plural: str,
    label: str,
    doc: str = ""
) -> t.Entity:
    """Build an ``Entity``.

    Args:
        key: Key to identify the ``Entity``.
        plural: The ``key`` pluralised.
        label: A summary description.
        doc: A full description.

    Returns:
        Entity.

    Raises:
        NotImplementedError: If ``roles`` is ``None``.

    Examples:
        >>> from openfisca_core import entities

        >>> entity = entities.build_entity(
        ...     "syndicate",
        ...     "syndicates",
        ...     "Banks loaning jointly.",
        ... )
        >>> entity
        Entity(syndicate)

        >>> entities.build_entity(
        ...     "company",
        ...     "companies",
        ...     "A small or medium company.",
        ... )
        Entity(company)

    """
    return Entity(
        key,
        plural,
        label,
        doc,
    )


def find_role(
    roles: Iterable[t.Role],
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
        >>> from openfisca_core import entities
        >>> from openfisca_core.entities import types as t

        >>> person_entity = entities.build_entity("person", "persons", "Person")

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

        >>> group_entity = entities.build_entity(
        ...     key="family",
        ...     plural="families",
        ...     label="Family",
        ...     doc="A Family represents a collection of related persons.",
        ... )

        >>> group_entity.add_roles(
        ...     person_entity,
        ...     roles=[principal, partner, parent],
        ... )

        >>> entities.find_role(group_entity.roles, "principal", total=1)
        Role(principal)

        >>> entities.find_role(group_entity.roles, "partner")
        Role(partner)

        >>> entities.find_role(group_entity.roles, "parent", total=2)
        Role(parent)

        >>> entities.find_role(group_entity.roles, "first_parent", total=1)
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
