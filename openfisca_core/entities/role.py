from __future__ import annotations

import dataclasses
import textwrap

from typing import Any, Iterator, Optional, Sequence, Tuple

from openfisca_core.types import (
    Personifiable,
    Rolifiable,
    RoleLike,
    )


@dataclasses.dataclass(init = False)
class Role:
    """Role of an :class:`.Entity` within a :class:`.GroupEntity`.

    Each :class:`.Entity` related to a :class:`.GroupEntity` has a
    :class:`.Role`. For example, if you have a family, its roles could include
    a parent, a child, and so on. Or if you have a tax household, its roles
    could include the taxpayer, a spouse, several dependents, and so on.

    Attributes:
        entity (:obj:`.GroupEntity`): Entity the :class:`.Role` belongs to.
        key (:obj:`str`): Key to identify the :class:`.Role`.
        plural (:obj:`str`, optional): The ``key``, pluralised.
        label (:obj:`str`, optional): A summary description.
        doc (:obj:`str`): A full description, dedented.
        max (:obj:`int`, optional): Max number of members. Defaults to None.
        subroles (list, optional): The ``subroles``. Defaults to None.

    Args:
        description: A dictionary containing most of the attributes.
        entity: :obj:`.Entity` the :class:`.Role` belongs to.

    Examples:
        >>> description = {
        ...     "key": "parent",
        ...     "label": "Parents",
        ...     "plural": "parents",
        ...     "doc": "The one or two adults in charge of the household.",
        ...     "max": 2,
        ...     }

        >>> role = Role(description, object())

        >>> repr(Role)
        "<class 'openfisca_core.entities.role.Role'>"

        >>> repr(role)
        '<Role(parent)>'

        >>> str(role)
        'parent'

        >>> dict(role)
        {'entity': <object object...>, 'key': 'parent', 'plural': 'parents'...}

        >>> list(role)
        [('entity', <object object...>), ('key', 'parent'), ('plural', 'par...]

        >>> role == role
        True

        >>> role != role
        False

    """

    __slots__ = ["entity", "key", "plural", "label", "doc", "max", "subroles"]
    entity: Personifiable
    key: str
    plural: Optional[str]
    label: Optional[str]
    doc: str
    max: Optional[int]
    subroles: Optional[Sequence[Rolifiable]]

    def __init__(self, description: RoleLike, entity: Personifiable) -> None:
        self.entity = entity
        self.key = description['key']
        self.plural = description.get('plural')
        self.label = description.get('label')
        self.doc = textwrap.dedent(str(description.get('doc', "")))
        self.max = description.get('max')
        self.subroles = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.key})>"

    def __str__(self) -> str:
        return self.key

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        return ((item, self.__getattribute__(item)) for item in self.__slots__)
