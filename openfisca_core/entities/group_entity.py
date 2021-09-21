import dataclasses
import textwrap
from typing import Any, Dict, Iterable, Optional, Sequence

from openfisca_core.types import Builder, RoleLike, SupportsRole

from ._role_builder import RoleBuilder
from .entity import Entity
from .role import Role


@dataclasses.dataclass(repr = False)
class GroupEntity(Entity):
    """Represents a :class:`.GroupEntity` on which calculations can be run.

    A :class:`.GroupEntity` is basically a group of people, and thus it is
    composed of several :obj:`Entity` with different :obj:`Role` within the
    group. For example a tax household, a family, a trust, etc.

    Attributes:
        key (:obj:`str`): Key to identify the :class:`.GroupEntity`.
        plural (:obj:`str`): The ``key``, pluralised.
        label (:obj:`str`): A summary description.
        doc (:obj:`str`): A full description, dedented.
        is_person (:obj:`bool`): Represents an individual? Defaults to False.

    Args:
        key: Key to identify the :class:`.GroupEntity`.
        plural: ``key``, pluralised.
        label: A summary description.
        doc: A full description.
        roles: The list of :class:`.Role` of the :class:`.GroupEntity`.

    Examples:
        >>> roles = [{
        ...     "key": "parent",
        ...     "subroles": ["first_parent", "second_parent"],
        ...     }]

        >>> group_entity = GroupEntity(
        ...     "household",
        ...     "households",
        ...     "A household",
        ...     "All the people who live together in the same place.",
        ...     roles,
        ...    )

        >>> repr(GroupEntity)
        "<class 'openfisca_core.entities.group_entity.GroupEntity'>"

        >>> repr(group_entity)
        '<GroupEntity(household)>'

        >>> str(group_entity)
        'households'

        >>> dict(group_entity)
        {'key': 'household', 'plural': 'households', 'label': 'A household...}

        >>> list(group_entity)
        [('key', 'household'), ('plural', 'households'), ('label', 'A hous...]

        >>> group_entity == group_entity
        True

        >>> group_entity != group_entity
        False

        :attr:`roles`

        >>> group_entity.roles
        (<Role(parent)>,)

        >>> group_entity.PARENT
        <Role(parent)>

        :attr:`flattened_roles`

        >>> group_entity.flattened_roles
        (<Role(first_parent)>, <Role(second_parent)>)

        >>> group_entity.FIRST_PARENT
        <Role(first_parent)>

    .. versionchanged:: 35.7.0
        Hereafter :attr:`.variables` allows querying a :obj:`.TaxBenefitSystem`
        for a :obj:`.Variable`.

    .. versionchanged:: 35.7.0
        Hereafter the equality of an :obj:`.GroupEntity` is determined by its
        data attributes.

    """

    __slots__ = [
        "key",
        "plural",
        "label",
        "doc",
        "is_person",
        "roles_description",
        "_population",
        "_tax_benefit_system",
        "_roles",
        "_roles_map",
        "_flattened_roles",
        ]

    __: dataclasses.InitVar[Iterable[RoleLike]]

    @property
    def roles(self) -> Sequence[SupportsRole]:
        """List of the roles of the group entity."""

        return self._roles

    @roles.setter
    def roles(self, roles: Sequence[SupportsRole]) -> None:
        self._roles = roles

    @property
    def flattened_roles(self) -> Sequence[SupportsRole]:
        """:attr:`roles` flattened out."""

        return self._flattened_roles

    @flattened_roles.setter
    def flattened_roles(self, roles: Sequence[SupportsRole]) -> None:
        self._flattened_roles = tuple(
            array
            for role in roles
            for array in role.subroles or [role]
            )

    def __post_init__(self, *__: Iterable[RoleLike]) -> None:
        self.doc = textwrap.dedent(self.doc)
        self.is_person = False

        # Extract roles.
        roles: Iterable[RoleLike]
        roles = next(iter(__))

        # Build roles & sub-roles.
        builder: Builder[GroupEntity, SupportsRole, RoleLike]
        builder = RoleBuilder(self, Role)
        self.roles = builder(roles)
        self.flattened_roles = self.roles

        # Assign role & sub-role attributes.
        self._roles_map: Dict[str, SupportsRole]
        self._roles_map = {}

        for role in (*self.roles, *self.flattened_roles):
            self._roles_map.update({role.key.upper(): role})

        # Useless step kept to avoid changing the signature.
        self.roles_description: Optional[Iterable[RoleLike]]
        self.roles_description = roles

    def __getattr__(self, attr: str) -> Any:
        if attr.isupper():
            return self._roles_map[attr]

        return self.__getattribute__(attr)
