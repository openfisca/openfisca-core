from openfisca_core import entities


class GroupEntity(entities.Entity):
    """
    Represents an entity composed of several persons with different roles, on which calculations are run.
    """

    def __init__(self, key, plural, label, doc, roles):
        super().__init__(key, plural, label, doc)
        self.roles_description = roles
        self.roles = []
        for role_description in roles:
            role = entities.Role(role_description, self)
            setattr(self, role.key.upper(), role)
            self.roles.append(role)
            if role_description.get('subroles'):
                role.subroles = []
                for subrole_key in role_description['subroles']:
                    subrole = entities.Role({'key': subrole_key, 'max': 1}, self)
                    setattr(self, subrole.key.upper(), subrole)
                    role.subroles.append(subrole)
                role.max = len(role.subroles)
        self.flattened_roles = sum([role2.subroles or [role2] for role2 in self.roles], [])
        self.is_person = False
