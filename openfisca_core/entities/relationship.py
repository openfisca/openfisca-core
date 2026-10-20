from collections.abc import Iterable, Sequence

from . import types as t
from .role import Role


class Relationship:
    def __init__(
        self, a: t.Entity, b: t.Entity, role_descriptions: Sequence[t.RoleParams]
    ):
        self.a: t.Entity = a
        self.b: t.Entity = b
        self.role_descriptions: Sequence[t.RoleParams] = role_descriptions
        roles = []
        for role_description in role_descriptions:
            role = Role(role_description, a)
            setattr(a, role.key.upper(), role)
            roles.append(role)
            if subroles := role_description.get("subroles"):
                role.subroles = ()
                for subrole_key in subroles:
                    subrole = Role({"key": subrole_key, "max": 1}, a)
                    setattr(a, subrole.key.upper(), subrole)
                    role.subroles = (*role.subroles, subrole)
                role.max = len(role.subroles)
        self.roles: Iterable[Role] = roles

    @property
    def name(self):
        return f"{self.a.key}_{self.b.key}"
