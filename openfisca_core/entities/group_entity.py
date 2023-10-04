from __future__ import annotations

from collections.abc import Iterable

from itertools import chain

from ._description import Description
from ._subrole import SubRole
from .entity import Entity
from .role import Role
from .typing import DescriptionParams


class GroupEntity(Entity):
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

    """  # noqa RST301

    #: A description of the GroupEntity.
    description: Description

    @property
    def key(self) -> str:
        """A key to identify the GroupEntity."""
        return self.description.key

    @property
    def plural(self) -> str | None:
        """The ``key``, pluralised."""
        return self.description.plural

    @property
    def label(self) -> str | None:
        """A summary description."""
        return self.description.label

    @property
    def doc(self) -> str | None:
        """A full description, non-indented."""
        return self.description.doc

    def __init__(
        self,
        key: str,
        plural: str,
        label: str,
        doc: str,
        roles: Iterable[DescriptionParams],
        containing_entities: Iterable[str] = (),
    ) -> None:
        self.description = Description(key, plural, label, doc)
        self.roles_description = roles
        self.roles = [self._build_role(description) for description in roles]
        self.flattened_roles = tuple(
            chain.from_iterable(role.subroles or [role] for role in self.roles)
        )
        self.is_person = False
        self.containing_entities = containing_entities

    def _build_role(self, description: DescriptionParams) -> Role:
        role = Role(entity=self, description=description)
        subroles = description.get("subroles")

        if subroles is not None:
            role.subroles = [self._build_subrole(role, key) for key in subroles]

            if len(subroles) > 0:
                role.max = len(role.subroles)

        setattr(self, role.key.upper(), role)

        return role

    def _build_subrole(self, role: Role, key: str) -> SubRole:
        subrole = SubRole(role, key)
        setattr(self, subrole.key.upper(), subrole)
        return subrole
