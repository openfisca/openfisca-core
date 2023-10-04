from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ._description import Description
from .typing import Entity, GroupEntity, SubRole


class Role:
    """The role of an Entity within a GroupEntity.

    Each Entity related to a GroupEntity has a Role. For example, if you have
    a family, its roles could include a parent, a child, and so on. Or if you
    have a tax household, its roles could include the taxpayer, a spouse,
    several dependents, and the like.

    Attributes:
        entity (Entity): The Entity the Role belongs to.
        description (Description): A description of the Role.
        max (int): Max number of members.
        subroles (list[Role]): A list of subroles.

    Args:
        description (dict): A description of the Role.
        entity (Entity): The Entity to which the Role belongs.

    Examples:
        >>> role = Role({"key": "parent"}, object())

        >>> repr(Role)
        "<class 'openfisca_core.entities.role.Role'>"

        >>> repr(role)
        'Role(parent)'

        >>> str(role)
        'Role(parent)'

        >>> {role}
        {Role(parent)}

        >>> role.key
        'parent'

    """

    #: The Entity the Role belongs to.
    entity: Entity | GroupEntity

    #: A description of the Role.
    description: Description

    #: Max number of members.
    max: int | None = None

    #: A list of subroles.
    subroles: Iterable[SubRole] | None = None

    @property
    def key(self) -> str:
        """A key to identify the Role."""
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
        self, description: Mapping[str, Any], entity: Entity | GroupEntity
    ) -> None:
        self.description = Description(
            **{
                key: value
                for key, value in description.items()
                if key in {"key", "plural", "label", "doc"}
            }
        )
        self.entity = entity
        self.max = description.get("max")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"
