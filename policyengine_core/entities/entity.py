import os
import textwrap
from typing import Any

from policyengine_core.entities.role import Role


class Entity:
    """
    Represents an entity (e.g. a person, a household, etc.) on which calculations can be run.
    """

    def __init__(self, key: str, plural: str, label: str, doc: str):
        self.key = key
        self.label = label
        self.plural = plural
        self.doc = textwrap.dedent(doc)
        self.is_person = True
        self._tax_benefit_system = None

    def set_tax_benefit_system(self, tax_benefit_system) -> None:
        self._tax_benefit_system = tax_benefit_system

    def check_role_validity(self, role: Any) -> None:
        if role is not None and not type(role) == Role:
            raise ValueError("{} is not a valid role".format(role))

    def get_variable(self, variable_name: str, check_existence: bool = False):
        return self._tax_benefit_system.get_variable(
            variable_name, check_existence
        )

    def check_variable_defined_for_entity(self, variable_name: str) -> None:
        variable_entity = self.get_variable(
            variable_name, check_existence=True
        ).entity
        # Should be this:
        # if variable_entity is not self:
        if variable_entity.key != self.key:
            message = os.linesep.join(
                [
                    "You tried to compute the variable '{0}' for the entity '{1}';".format(
                        variable_name, self.plural
                    ),
                    "however the variable '{0}' is defined for '{1}'.".format(
                        variable_name, variable_entity.plural
                    ),
                    "Learn more about entities in our documentation:",
                    "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>.",
                ]
            )
            raise ValueError(message)
