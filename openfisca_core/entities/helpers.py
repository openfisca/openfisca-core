from __future__ import annotations

import warnings
from collections.abc import Sequence

from . import types as t
from .entity import Entity


class DeprecatedEntityManager:
    def __init__(self):
        super(DeprecatedEntityManager).__init__()
        self.group_entities_with_roles = []
        self.person_entity = None

    def add_entity(
        self: DeprecatedEntityManager,
        key: str,
        plural: str,
        label: str,
        doc: str = "",
        roles: None | Sequence[t.RoleParams] = None,
        is_person: bool = False,
    ):
        new_entity = Entity(key, plural, label, doc)

        if is_person:
            if self.person_entity:
                raise ValueError(
                    "Only one entity can be defined with is_person. Exiting…"
                )
            self.person_entity = new_entity

            for entity, entity_roles in self.group_entities_with_roles:
                if entity_roles:
                    entity.add_relationship(self.person_entity, entity_roles)
        else:
            self.group_entities_with_roles.append((new_entity, roles))
            if roles and self.person_entity:
                new_entity.add_relationship(self.person_entity, roles)

        return new_entity


default_manager = DeprecatedEntityManager()


def build_entity(
    key: str,
    plural: str,
    label: str,
    doc: str = "",
    roles: None | Sequence[t.RoleParams] = None,
    is_person: bool = False,
) -> t.Entity:
    message = """build_entity has been deprecated in 47.0.0. It will be removed in the future."""
    warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)

    return default_manager.add_entity(key, plural, label, doc, roles, is_person)


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
        <openfisca_core.entities.entity.Relationship object at ...>

        >>> find_role(group_entity, "principal", total=1)
        (Role(principal), <openfisca_core.entities.entity.Relationship object at ...>)

        >>> find_role(group_entity, "partner")
        (Role(partner), <openfisca_core.entities.entity.Relationship object at ...>)

        >>> find_role(group_entity, "parent", total=2)
        (Role(parent), <openfisca_core.entities.entity.Relationship object at ...>)

        >>> find_role(group_entity, "first_parent", total=1)
        (Role(first_parent), <openfisca_core.entities.entity.Relationship object at ...>)

    """
    for relationship in entity.relationships:
        if relationship.b == entity:
            continue
        for role in relationship.roles:
            if role.subroles:
                for subrole in role.subroles:
                    if (subrole.max == total) and (subrole.key == key):
                        return subrole, relationship

            if (role.max == total) and (role.key == key):
                return role, relationship

    return None, None


def reset_entity_manager():
    global default_manager
    default_manager = DeprecatedEntityManager()


build_entity.reset_entity_manager = reset_entity_manager

__all__ = ["build_entity", "find_role"]
