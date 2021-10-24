from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence
from openfisca_core.typing import RoleProtocol, RoleSchema

import dataclasses
from itertools import chain

from .entity import Entity
from .role import Role


@dataclasses.dataclass
class GroupEntity(Entity):
    """Represents an entity containing several others with different roles.

    A :class:`.GroupEntity` represents an :class:`.Entity` containing
    several other :class:`.Entity` with different :class:`.Role`, and on
    which calculations can be run.

    Attributes:
        key:
            Key to identify the :class:`.GroupEntity`.
        plural:
            The ``key``, pluralised.
        label:
            A summary description.
        doc:
            A full description, dedented.
        is_person:
            Represents an individual? Defaults to False.
        roles:
            List of the roles of the group entity.
        flattened_roles:
            ``roles`` flattened out.
        containing_entities:
            Keys of :obj:`.GroupEntity` whose members are guaranteed to be a
            superset of this group's entities.

    Args:
        key:
            Key to identify the :class:`.GroupEntity`.
        plural:
            The ``key``, pluralised.
        label:
            A summary description.
        doc:
            A full description, dedented.
        roles:
            The list of :class:`.Role` of the :class:`.GroupEntity`.
        containing_entities:
            The list of keys of :obj:`.GroupEntity` whose members are
            guaranteed to be a superset of this group's entities.

    Examples:
        >>> family_roles = [{
        ...     "key": "parent",
        ...     "subroles": ["first_parent", "second_parent"],
        ...     }]

        >>> family = GroupEntity(
        ...     "family",
        ...     "families",
        ...     "A family",
        ...     "All the people somehow related living together.",
        ...     family_roles,
        ...    )

        >>> household_roles = [{
        ...     "key": "partners",
        ...     "subroles": ["first_partner", "second_partner"],
        ...     }]

        >>> household = GroupEntity(
        ...     "household",
        ...     "households",
        ...     "A household",
        ...     "All the people who live together in the same place.",
        ...     household_roles,
        ...     (family.key,),
        ...    )

        >>> repr(GroupEntity)
        "<class 'openfisca_core.entities.group_entity.GroupEntity'>"

        >>> repr(household)
        'GroupEntity(household)'

        >>> str(household)
        'households'

    .. versionchanged:: 35.8.0
        Added documentation, doctests, and typing.

    .. versionchanged:: 35.7.0
        Added ``containing_entities``, that allows the defining of group
        entities which entirely contain other group entities.

    """

    __slots__ = tuple((
        "_cached_roles",
        "_tax_benefit_system",
        "containing_entities",
        "doc",
        "flattened_roles",
        "is_person",
        "key",
        "label",
        "plural",
        "roles",
        "roles_description",
        ))

    is_person: bool
    roles: Sequence[RoleProtocol]
    containing_entities: Sequence[str]
    flattened_roles: Sequence[RoleProtocol]
    roles_description: Sequence[RoleSchema]
    _cached_roles: Dict[str, RoleProtocol]

    def __init__(
            self,
            key: str,
            plural: str,
            label: str,
            doc: str,
            roles: Sequence[RoleSchema],
            containing_entities: Sequence[str] = (),
            ):

        super().__init__(key, plural, label, doc)
        self.containing_entities = containing_entities
        self.roles = tuple(_build_role(self, desc) for desc in roles)
        self.flattened_roles = _flatten_roles(self.roles)
        self.roles_description = roles
        self._cached_roles = _cache_roles((*self.roles, *self.flattened_roles))

    def __getattr__(self, attr: str) -> Any:
        if attr.isupper():
            role = self._cached_roles.get(attr)

            if role is not None:
                return role

        return self.__getattribute__(attr)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def __str__(self) -> str:
        return self.plural


def _build_role(entity: GroupEntity, description: RoleSchema) -> Role:
    """Build roles & sub-roles.

    Args:
        entity: A :obj:`.GroupEntity`.
        description: A :obj:`dict` to build a :obj:`.Role`.

    Returns:
        Role.

    Examples:
        >>> description = {"key": "key"}
        >>> _build_role(object(), description)
        Role(key)

        >>> _build_role(object(), {})
        Traceback (most recent call last):
        KeyError: 'key'

    .. versionadded:: 35.8.0

    """

    role = Role(description, entity)
    subroles = description.get("subroles", ())

    if subroles:
        role.subroles = ()

        for key in subroles:
            subrole = Role({"key": key, "max": 1}, entity)
            role.subroles = (*role.subroles, subrole)

        role.max = len(role.subroles)

    return role


def _flatten_roles(roles: Sequence[RoleProtocol]) -> Sequence[RoleProtocol]:
    """Flattens roles' subroles to a sequence.

    Args:
        roles: A list of :obj:`.Role`.

    Returns:
        A list of subroles.

    Examples:
        >>> _flatten_roles([])
        ()

        >>> role = Role({"key": "key"}, object())
        >>> _flatten_roles([role])
        (Role(key),)

        >>> role.subroles = role,
        >>> _flatten_roles([role])
        (Role(key),)

        >>> subrole = Role({"key": "llave"}, object())
        >>> role.subroles += subrole,
        >>> _flatten_roles([role])
        (Role(key), Role(llave))

    .. versionadded:: 35.8.0

    """

    tree: Iterable[Iterable[RoleProtocol]]
    tree = [role.subroles or [role] for role in roles]

    return tuple(chain.from_iterable(tree))


def _cache_roles(roles: Sequence[RoleProtocol]) -> Dict[str, RoleProtocol]:
    """Create a cached dictionary of :obj:`.Role`.

    Args:
        roles: The :obj:`.Role` to cache.

    Returns:
        Dictionary with the cached :obj:`.Role`.

    Examples:
        >>> role = Role({"key": "key"}, object())
        >>> _cache_roles([role])
        {'KEY': Role(key)}

    .. versionadded:: 35.8.0

    """

    return {role.key.upper(): role for role in roles}
