# -*- coding: utf-8 -*-

import textwrap
from os import linesep


class Role(object):

    def __init__(self, description, entity):
        self.entity = entity
        self.key = description['key']
        self.label = description.get('label')
        self.plural = description.get('plural')
        self.doc = textwrap.dedent(description.get('doc', ""))
        self.max = description.get('max')
        self.subroles = None

    def __repr__(self):
        return "Role({})".format(self.key)


class Entity(object):
    """
        Represents an entity (e.g. a person, a household, etc.) on which calculations can be run.
    """

    def __init__(self, key, plural, label, doc):
        self.key = key
        self.label = label
        self.plural = plural
        self.doc = textwrap.dedent(doc)
        self.is_person = True
        self._tax_benefit_system = None

    def set_tax_benefit_system(self, tax_benefit_system):
        self._tax_benefit_system = tax_benefit_system

    def check_role_validity(self, role):
        if role is not None and not type(role) == Role:
            raise ValueError("{} is not a valid role".format(role))

    def get_variable(self, variable_name, check_existence = False):
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name):
        variable_entity = self.get_variable(variable_name, check_existence = True).entity
        # Should be this:
        # if variable_entity is not self:
        if variable_entity.key != self.key:
            message = linesep.join([
                "You tried to compute the variable '{0}' for the entity '{1}';".format(variable_name, self.plural),
                "however the variable '{0}' is defined for '{1}'.".format(variable_name, variable_entity.plural),
                "Learn more about entities in our documentation:",
                "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
            raise ValueError(message)


class GroupEntity(Entity):
    """
        Represents an entity composed of several persons with different roles, on which calculations are run.
    """

    def __init__(self, key, plural, label, doc, roles):
        super().__init__(key, plural, label, doc)
        self.roles_description = roles
        self.roles = []
        for role_description in roles:
            role = Role(role_description, self)
            setattr(self, role.key.upper(), role)
            self.roles.append(role)
            if role_description.get('subroles'):
                role.subroles = []
                for subrole_key in role_description['subroles']:
                    subrole = Role({'key': subrole_key, 'max': 1}, self)
                    setattr(self, subrole.key.upper(), subrole)
                    role.subroles.append(subrole)
                role.max = len(role.subroles)
        self.flattened_roles = sum([role2.subroles or [role2] for role2 in self.roles], [])
        self.is_person = False


def build_entity(key, plural, label, doc = "", roles = None, is_person = False, class_override = None):
    if is_person:
        return Entity(key, plural, label, doc)
    else:
        return GroupEntity(key, plural, label, doc, roles)
