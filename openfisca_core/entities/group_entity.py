from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import ClassVar

import textwrap
from itertools import chain

from . import types as t
from ._core_entity import CoreEntity
from .role import Role


class GroupEntity(CoreEntity):
    r"""Represents an entity containing several others with different roles.

    A ``GroupEntity`` represents an ``Entity`` containing several other entities,
    with different roles, and on which calculations can be run.

    Args:
        key: A key to identify the ``GroupEntity``.
        plural: The ``key`` pluralised.
        label: A summary description.
        doc: A full description.
        roles: The list of roles of the group entity.
        containing_entities: The list of keys of group entities whose members
            are guaranteed to be a superset of this group's entities.

    Examples:
        >>> from openfisca_core import entities

        >>> family_roles = [
        ...     {
        ...         "key": "parent",
        ...         "subroles": ["first_parent", "second_parent"],
        ...     }
        ... ]

        >>> family = entities.GroupEntity(
        ...     "family",
        ...     "families",
        ...     "A family",
        ...     "\t\t\tAll the people somehow related living together.",
        ...     family_roles,
        ... )

        >>> household_roles = [
        ...     {
        ...         "key": "partners",
        ...         "subroles": ["first_partner", "second_partner"],
        ...     }
        ... ]

        >>> household = entities.GroupEntity(
        ...     "household",
        ...     "households",
        ...     "A household",
        ...     "\t\t\tAll the people who live together in the same place.",
        ...     household_roles,
        ...     (family.key,),
        ... )

        >>> repr(entities.GroupEntity)
        "<class 'openfisca_core.entities.group_entity.GroupEntity'>"

        >>> repr(household)
        'GroupEntity(household)'

        >>> str(household)
        'GroupEntity(household)'

    """

    #: A key to identify the ``Entity``.
    key: t.EntityKey

    #: The ``key`` pluralised.
    plural: t.EntityPlural

    #: A summary description.
    label: str

    #: A full description.
    doc: str

    #: The list of roles of the ``GroupEntity``.
    roles: Iterable[Role]

    #: Whether the entity is a person or not.
    is_person: ClassVar[bool] = False

    def __init__(
        self,
        key: str,
        plural: str,
        label: str,
        doc: str,
        roles: Sequence[t.RoleParams],
        containing_entities: Iterable[str] = (),
    ) -> None:
        self.key = t.EntityKey(key)
        self.plural = t.EntityPlural(plural)
        self.label = label
        self.doc = textwrap.dedent(doc)
        self.roles_description = roles
        self.roles: Iterable[Role] = ()
        for role_description in roles:
            role = Role(role_description, self)
            setattr(self, role.key.upper(), role)
            self.roles = (*self.roles, role)
            if subroles := role_description.get("subroles"):
                role.subroles = ()
                for subrole_key in subroles:
                    subrole = Role({"key": subrole_key, "max": 1}, self)
                    setattr(self, subrole.key.upper(), subrole)
                    role.subroles = (*role.subroles, subrole)
                role.max = len(role.subroles)
        self.flattened_roles = tuple(
            chain.from_iterable(role.subroles or [role] for role in self.roles),
        )
        self.containing_entities = containing_entities


__all__ = ["GroupEntity"]
