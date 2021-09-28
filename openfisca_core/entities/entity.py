import os
import textwrap

from openfisca_core.entities import Role


class Entity:
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

    @staticmethod
    def check_role_validity(role):
        if role is not None and not isinstance(role, Role):
            raise ValueError(f"{role} is not a valid role")

    def get_variable(self, variable_name, check_existence = False):
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name):
        variable_entity = self.get_variable(variable_name, check_existence = True).entity
        # Should be this:
        # if variable_entity is not self:
        if variable_entity.key != self.key:
            message = os.linesep.join([
                f"You tried to compute the variable '{variable_name}' for the entity '{self.plural}';",
                f"however the variable '{variable_name}' is defined for '{variable_entity.plural}'.",
                "Learn more about entities in our documentation:",
                "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
            raise ValueError(message)
