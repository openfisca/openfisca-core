from __future__ import annotations

from typing import Iterable, Sequence, Type

from openfisca_core.types import Personifiable, Rolifiable, RoleLike


class RoleBuilder:
    """Builds roles & sub-roles from a given input.

    Attributes:
        builder (:obj:`Personifiable`):
            A builder object, like a :class:`.GroupEntity` for example.
        buildee (:obj:`Rolifiable`):
            The objects to be built, in this case :class:`.Role`.

    Args:
        builder: A builder object, like a :class:`.GroupEntity` for example.
        buildee: The objects to be built, in this case :class:`.Role`.

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
        >>> builder(items)
        [Role(parent)]

    .. versionadded:: 35.5.0

    """

    def __init__(
            self,
            builder: Personifiable,
            buildee: Type[Rolifiable],
            ) -> None:
        self.builder = builder
        self.buildee = buildee

    def __call__(self, items: Iterable[RoleLike]) -> Sequence[Rolifiable]:
        """Builds a sub/role for each item in ``items``.

        Args:
            items: Role-like items, see :class:`.RoleLike`.

        Returns:
            A :obj:`list` of :obj:`.Role`.

        """

        return [self.build(item) for item in items]

    def build(self, item: RoleLike) -> Rolifiable:
        """Builds a role from ``item``.

        Args:
            item: A role-like item, see :class:`.RoleLike`.

        Returns:
            A role.

        """

        role = self.buildee(item, self.builder)
        self.builder.__dict__[role.key.upper()] = role
        subroles = item.get("subroles", [])

        if subroles:
            role.subroles = [self.build(RoleLike({"key": key, "max": 1})) for key in subroles]
            role.max = len(role.subroles)

        return role
