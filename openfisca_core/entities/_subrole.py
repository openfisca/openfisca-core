from __future__ import annotations

import dataclasses

from .typing import Entity, GroupEntity, Role


@dataclasses.dataclass(frozen=True)
class SubRole:
    """The sub-role of a Role.

    Each Role can be composed of one or several SubRole. For example, if you
    have a Role "parent", its sub-roles could include "mother" and "father".

    Attributes:
        role (Role): The Role the SubRole belongs to.
        key (str): A key to identify the SubRole.
        max (int): Max number of members.

    Args:
        role (Role): The Role the SubRole belongs to.
        key (str): A key to identify the SubRole.

    Examples:
        >>> from openfisca_core import entities

        >>> entity = entities.GroupEntity("person", "", "", "", [])
        >>> role = entities.Role({"key": "sorority"}, entity)
        >>> subrole = SubRole(role, "sister")

        >>> repr(SubRole)
        "<class 'openfisca_core.entities._subrole.SubRole'>"

        >>> repr(subrole)
        "SubRole(role=Role(sorority), key='sister', max=1)"

        >>> str(subrole)
        "SubRole(role=Role(sorority), key='sister', max=1)"

        >>> {subrole}
        {SubRole(role=Role(sorority), key='sister', max=1)}

        >>> subrole.entity.key
        'person'

        >>> subrole.role.key
        'sorority'

        >>> subrole.key
        'sister'

        >>> subrole.max
        1

    .. versionadded:: 41.2.0

    """

    #: An id to identify the Role the SubRole belongs to.
    role: Role

    #: A key to identify the SubRole.
    key: str

    #: Max number of members.
    max: int = 1

    @property
    def entity(self) -> Entity | GroupEntity:
        """The Entity the SubRole transitively belongs to."""
        return self.role.entity
