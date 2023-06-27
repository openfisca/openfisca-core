from __future__ import annotations

import dataclasses
import textwrap


class Role:
    """The role of an Entity within a GroupEntity.

    Each Entity related to a GroupEntity has a Role. For example, if you have
    a family, its roles could include a parent, a child, and so on. Or if you
    have a tax household, its roles could include the taxpayer, a spouse,
    several dependents, and the like.

    """

    def __init__(self, description, entity):
        self.entity = entity
        self.key = description["key"]
        self.label = description.get("label")
        self.plural = description.get("plural")
        self.doc = textwrap.dedent(description.get("doc", ""))
        self.max = description.get("max")
        self.subroles = None

    def __repr__(self) -> str:
        return "Role({})".format(self.key)


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
    plural: str | None

    #: A summary description.
    label: str | None

    #: A full description, dedented.
    doc: str = ""

    #: Max number of members.
    max: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "doc", textwrap.dedent(self.doc))
