from __future__ import annotations

from collections.abc import Iterable, Sequence

import textwrap
from itertools import chain

from . import types as t
from ._core_entity import _CoreEntity
from .role import Role


class GroupEntity(_CoreEntity):
    """Represents an entity containing several others with different roles.

    A :class:`.GroupEntity` represents an :class:`.Entity` containing
    several other :class:`.Entity` with different :class:`.Role`, and on
    which calculations can be run.

    Args:
        key: A key to identify the group entity.
        plural: The ``key``, pluralised.
        label: A summary description.
        doc: A full description.
        roles: The list of :class:`.Role` of the group entity.
        containing_entities: The list of keys of group entities whose members
            are guaranteed to be a superset of this group's entities.

    """

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
        self.label = label
        self.plural = t.EntityPlural(plural)
        self.doc = textwrap.dedent(doc)
        self.is_person = False
        self.roles_description = roles
        self.roles: Iterable[Role] = ()
        for role_description in roles:
            role = Role(role_description, self)
            setattr(self, role.key.upper(), role)
            self.roles = (*self.roles, role)
            if role_description.get("subroles"):
                role.subroles = ()
                for subrole_key in role_description["subroles"]:
                    subrole = Role({"key": subrole_key, "max": 1}, self)
                    setattr(self, subrole.key.upper(), subrole)
                    role.subroles = (*role.subroles, subrole)
                role.max = len(role.subroles)
        self.flattened_roles = tuple(
            chain.from_iterable(role.subroles or [role] for role in self.roles),
        )

        self.is_person = False
        self.containing_entities = containing_entities
