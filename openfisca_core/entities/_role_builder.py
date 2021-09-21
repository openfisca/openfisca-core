from __future__ import annotations

import dataclasses
from typing import Iterable, Optional, Sequence, Type

from openfisca_core.types import HasPlural, RoleLike, SupportsRole


@dataclasses.dataclass(frozen = True)
class RoleBuilder:
    """Builds roles & sub-roles from a given input.

    Attributes:
        builder (:obj:`.Entity` or :obj:`.GroupEntity`):
            A builder object.
        buildee (:obj:`.Role`):
            The objects to be built.

    Args:
        builder: A builder object.
        buildee: The objects to be built.

    Examples:
        >>> from openfisca_core.entities import GroupEntity, Role

        >>> group_entity = GroupEntity(
        ...     "household",
        ...     "households",
        ...     "A household",
        ...     "All the people who live together in the same place.",
        ...     []
        ...    )

        >>> items = [{
        ...     "key": "parent",
        ...     "subroles": ["first_parent", "second_parent"],
        ...     }]

        >>> builder = RoleBuilder(group_entity, Role)

        >>> repr(RoleBuilder)
        "<class 'openfisca_core.entities._role_builder.RoleBuilder'>"

        >>> repr(builder)
        "<RoleBuilder(households, <class '...Role'>)>"

        >>> str(builder)
        "<RoleBuilder(households, <class '...Role'>)>"

        >>> builder(items)
        [<Role(parent)>]

    .. versionadded:: 35.7.0

    """

    __slots__ = ["builder", "buildee"]
    builder: HasPlural
    buildee: Type[SupportsRole]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.builder}, {self.buildee})>"

    def __call__(self, items: Iterable[RoleLike]) -> Sequence[SupportsRole]:
        """Builds a sub/role for each item in ``items``.

        Args:
            items: Role-like items, see :class:`.RoleLike`.

        Returns:
            A :obj:`list` of :obj:`.Role`.

        .. versionadded:: 35.7.0

        """

        return [self.build(item) for item in items]

    def build(self, item: RoleLike) -> SupportsRole:
        """Builds a role from ``item``.

        Args:
            item: A role-like item, see :class:`.RoleLike`.

        Returns:
            :obj:`.Role`: A :obj:`.Role`.

        .. versionadded:: 35.7.0

        """

        role: SupportsRole
        subroles: Optional[Iterable[str]]

        role = self.buildee(item, self.builder)
        subroles = item.get("subroles", [])

        if subroles:
            role.subroles = [
                self.build(RoleLike({"key": key, "max": 1}))
                for key in subroles
                ]
            role.max = len(role.subroles)

        return role
