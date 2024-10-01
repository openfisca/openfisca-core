from __future__ import annotations

from collections.abc import Iterable

from . import types as t
from ._description import _Description


class Role:
    """The role of an ``Entity`` within a ``GroupEntity``.

    Each ``Entity`` related to a ``GroupEntity`` has a ``Role``. For example,
    if you have a family, its roles could include a parent, a child, and so on.
    Or if you have a tax household, its roles could include the taxpayer, a
    spouse, several dependents, and the like.

    Args:
        description: A description of the Role.
        entity: The Entity to which the Role belongs.

    Examples:
        >>> from openfisca_core import entities
        >>> entity = entities.GroupEntity("key", "plural", "label", "doc", [])
        >>> role = entities.Role({"key": "parent"}, entity)

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

    #: The ``GroupEntity`` the Role belongs to.
    entity: t.GroupEntity

    #: A description of the ``Role``.
    description: _Description

    #: Max number of members.
    max: None | int = None

    #: A list of subroles.
    subroles: None | Iterable[Role] = None

    @property
    def key(self) -> t.RoleKey:
        """A key to identify the ``Role``."""
        return t.RoleKey(self.description.key)

    @property
    def plural(self) -> None | t.RolePlural:
        """The ``key`` pluralised."""
        if (plural := self.description.plural) is None:
            return None
        return t.RolePlural(plural)

    @property
    def label(self) -> None | str:
        """A summary description."""
        return self.description.label

    @property
    def doc(self) -> None | str:
        """A full description, non-indented."""
        return self.description.doc

    def __init__(self, description: t.RoleParams, entity: t.GroupEntity) -> None:
        self.description = _Description(
            key=description["key"],
            plural=description.get("plural"),
            label=description.get("label"),
            doc=description.get("doc"),
        )
        self.entity = entity
        self.max = description.get("max")

    def __repr__(self) -> str:
        return f"Role({self.key})"


__all__ = ["Role"]
