import dataclasses
import textwrap
import typing
from typing import Iterable, Sequence

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
        roles (:obj:`list` of :obj:`.Role`): List of the roles of the entity.
        roles_description(:obj:`list` of :obj:`dict`): List of roles to build.
        flattened_roles(:obj:`list` of :obj:`.Role`): ``roles`` flattened out.
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
        ...     roles
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

    .. versionchanged:: 35.7.0
        Hereafter ``variables`` allows querying a :obj:`.TaxBenefitSystem`
        for a :obj:`.Variable`.

    .. versionchanged:: 35.7.0
        Hereafter the equality of an :obj:`.GroupEntity` is determined by its
        data attributes.

    """

    roles: Iterable[RoleLike]

    def __post_init__(self) -> None:
        self.doc = textwrap.dedent(self.doc)
        self.is_person = False

        # Useless step kept to avoid changing the signature.
        self.roles_description: Iterable[RoleLike]
        self.roles_description = self.roles

        # Create builder.
        builder: Builder[GroupEntity, SupportsRole, RoleLike]
        builder = RoleBuilder(self, Role)

        # Build roles & assign role attributes.
        roles: Sequence[SupportsRole]
        roles = builder(self.roles)

        # Not true, but we have to "fake" the type here, as the method is not
        # pure. Otherwise we would have to change the signature of the method.
        self.roles = typing.cast(Iterable[RoleLike], roles)

        for role in roles:
            self.__dict__.update({role.key.upper(): role})

        # Assign sub-role attributes.
        self.flattened_roles: Sequence[SupportsRole]
        self.flattened_roles = self._flatten(roles)

        for role in self.flattened_roles:
            self.__dict__.update({role.key.upper(): role})

        # Just for the record.
        typing.cast(Sequence[SupportsRole], self.roles)

    @staticmethod
    def _flatten(roles: Sequence[SupportsRole]) -> Sequence[SupportsRole]:
        return [array for role in roles for array in role.subroles or [role]]
