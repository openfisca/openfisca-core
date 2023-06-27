from __future__ import annotations

from typing import Any

import dataclasses
import textwrap

from openfisca_core.types import Entity


class Role:
    """The role of an Entity within a GroupEntity.

    Each Entity related to a GroupEntity has a Role. For example, if you have
    a family, its roles could include a parent, a child, and so on. Or if you
    have a tax household, its roles could include the taxpayer, a spouse,
    several dependents, and the like.

    Attributes:
        entity (Entity): The Entity to which the Role belongs.
        subroles (list[Role]): A list of subroles.
        description (RoleDescription): A description of the Role.

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

        >>> role.key
        'parent'

    .. versionchanged:: 40.1.0
        Added documentation, doctests, and typing.

    """

    def __init__(self, description: dict[str, Any], entity: Entity) -> None:
        self.entity: Entity = entity
        self.subroles: list[Role] | None = None
        self.description: RoleDescription = RoleDescription(**description)

    def __repr__(self) -> str:
        return "Role({})".format(self.key)

    def __getattr__(self, attr: str) -> Any:
        if hasattr(self.description, attr):
            return getattr(self.description, attr)

        raise AttributeError


@dataclasses.dataclass(frozen=True)
class RoleDescription:
    """A Role's description.

    Examples:
        >>> description = {
        ...     "key": "parent",
        ...     "label": "Parents",
        ...     "plural": "parents",
        ...     "doc": "\t\t\tThe one/two adults in charge of the household.",
        ...     "max": 2,
        ... }

        >>> role_description = RoleDescription(**description)

        >>> repr(RoleDescription)
        "<class 'openfisca_core.entities.role.RoleDescription'>"

        >>> repr(role_description)
        "RoleDescription(key='parent', plural='parents', label='Parents', ...)"

        >>> str(role_description)
        "RoleDescription(key='parent', plural='parents', label='Parents', ...)"

        >>> role_description.key
        'parent'

    .. versionadded:: 40.1.0

    """

    #: A key to identify the Role.
    key: str

    #: The ``key``, pluralised.
    plural: str | None = None

    #: A summary description.
    label: str | None = None

    #: A full description, dedented.
    doc: str = ""

    #: Max number of members.
    max: int | None = None

    #: A list of subroles.
    subroles: list[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "doc", textwrap.dedent(self.doc))
