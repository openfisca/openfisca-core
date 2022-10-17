from typing import List

from policyengine_core.entities.entity import Entity
from policyengine_core.entities.role import Role


class GroupEntity(Entity):
    """Represents an entity containing several others with different roles.

    A :class:`.GroupEntity` represents an :class:`.Entity` containing
    several other :class:`.Entity` with different :class:`.Role`, and on
    which calculations can be run.

    Args:
        key: A key to identify the group entity.
        plural: The ``key``, pluralised.
        label: A summary description.
        doc: A full description.
        roles: The list of :class:`.Role` of the group entity.
        containing_entities: The list of keys of group entities whose members
            are guaranteed to be a superset of this group's entities.

    .. versionchanged:: 35.7.0
        Added ``containing_entities``, that allows the defining of group
        entities which entirely contain other group entities.

    """

    def __init__(
        self,
        key: str,
        plural: str,
        label: str,
        doc: str,
        roles: List[str],
        containing_entities: List[str] = (),
    ):
        super().__init__(key, plural, label, doc)
        self.roles_description = roles
        self.roles = []
        for role_description in roles:
            role = Role(role_description, self)
            setattr(self, role.key.upper(), role)
            self.roles.append(role)
            if role_description.get("subroles"):
                role.subroles = []
                for subrole_key in role_description["subroles"]:
                    subrole = Role({"key": subrole_key, "max": 1}, self)
                    setattr(self, subrole.key.upper(), subrole)
                    role.subroles.append(subrole)
                role.max = len(role.subroles)
        self.flattened_roles = sum(
            [role2.subroles or [role2] for role2 in self.roles], []
        )
        self.is_person = False
        self.containing_entities = containing_entities
