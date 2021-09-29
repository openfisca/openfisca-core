from typing import Iterable, Sequence

from openfisca_core.types import Buildable, Rolifiable, RoleLike

from .entity import Entity
from .role import Role
from .role_builder import RoleBuilder


class GroupEntity(Entity):
    """Represents a :class:`.GroupEntity` on which calculations can be run.

    A :class:`.GroupEntity` is basically a group of people, and thus it is
    composed of several :obj:`Entitity` with different :obj:`Role` within the
    group. For example a tax household, a family, a trust, etc.

    Attributes:
        key (:obj:`str`): Key to identify the :class:`.GroupEntity`.
        plural (:obj:`str`): The :attr:`key`, pluralised.
        label (:obj:`str`): A summary description.
        doc (:obj:`str`): A full description, dedented.
        is_person (:obj:`bool`): If is an individual or not. Defaults to False.
        roles_description(:obj:`List[dict]`): A list of the role attributes.
        roles (:obj:`List[Role]`): A list of the roles of the group entity.
        flattened_roles(:obj:`List[Role]`): :attr:`.roles` flattened out.

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
        >>> GroupEntity(
        ...     "household",
        ...     "households",
        ...     "A household",
        ...     "All the people who live together in the same place.",
        ...     roles
        ...    )
        <openfisca_core.entities.group_entity.GroupEntity...

    """

    key: str
    plural: str
    label: str
    doc: str
    is_person: bool = False
    roles_description: Iterable[RoleLike]
    roles: Sequence[Rolifiable]
    flattened_roles: Sequence[Rolifiable]

    def __init__(
            self,
            key: str,
            plural: str,
            label: str,
            doc: str,
            roles: Iterable[RoleLike],
            ) -> None:
        super().__init__(key, plural, label, doc)
        builder: Buildable[GroupEntity, Rolifiable, RoleLike]
        builder = RoleBuilder(self, Role)
        self.roles_description = roles
        self.roles = builder(roles)
        self.flattened_roles = sum([role2.subroles or [role2] for role2 in self.roles], [])
