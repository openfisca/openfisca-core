from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dataclasses
import textwrap

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .types import SingleEntity


class Role:
    """The role of an Entity within a GroupEntity.

    Each Entity related to a GroupEntity has a Role. For example, if you have
    a family, its roles could include a parent, a child, and so on. Or if you
    have a tax household, its roles could include the taxpayer, a spouse,
    several dependents, and the like.

    Attributes:
        entity (Entity): The Entity the Role belongs to.
        description (_Description): A description of the Role.
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
    entity: SingleEntity

    #: A description of the Role.
    description: _Description

    #: Max number of members.
    max: int | None = None

    #: A list of subroles.
    subroles: Iterable[Role] | None = None

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

    def __init__(self, description: Mapping[str, Any], entity: SingleEntity) -> None:
        self.description = _Description(
            **{
                key: value
                for key, value in description.items()
                if key in {"key", "plural", "label", "doc"}
            },
        )
        self.entity = entity
        self.max = description.get("max")

    def __repr__(self) -> str:
        return f"Role({self.key})"


@dataclasses.dataclass(frozen=True)
class _Description:
    r"""A Role's description.

    Examples:
        >>> data = {
        ...     "key": "parent",
        ...     "label": "Parents",
        ...     "plural": "parents",
        ...     "doc": "\t\t\tThe one/two adults in charge of the household.",
        ... }

        >>> description = _Description(**data)

        >>> repr(_Description)
        "<class 'openfisca_core.entities.role._Description'>"

        >>> repr(description)
        "_Description(key='parent', plural='parents', label='Parents', ...)"

        >>> str(description)
        "_Description(key='parent', plural='parents', label='Parents', ...)"

        >>> {description}
        {_Description(key='parent', plural='parents', label='Parents', doc=...}

        >>> description.key
        'parent'

    .. versionadded:: 41.0.1

    """

    #: A key to identify the Role.
    key: str

    #: The ``key``, pluralised.
    plural: str | None = None

    #: A summary description.
    label: str | None = None

    #: A full description, non-indented.
    doc: str | None = None

    def __post_init__(self) -> None:
        if self.doc is not None:
            object.__setattr__(self, "doc", textwrap.dedent(self.doc))
