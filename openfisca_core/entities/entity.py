from openfisca_core.types import TaxBenefitSystem, Variable
from typing import Any, Optional

import os
import textwrap

from .role import Role


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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entity):
            return self.key == other.key

        return NotImplemented

    def set_tax_benefit_system(self, tax_benefit_system: TaxBenefitSystem):
        self._tax_benefit_system = tax_benefit_system

    def check_role_validity(self, role: Any) -> None:
        if role is not None and not isinstance(role, Role):
            raise ValueError(f"{role} is not a valid role")

    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> Optional[Variable]:
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name: str) -> None:
        variable: Optional[Variable]
        entity: Entity

        variable = self.get_variable(variable_name, check_existence=True)

        if variable is not None:
            entity = variable.entity

        if self != entity:
            message = os.linesep.join(
                [
                    f"You tried to compute the variable '{variable_name}' for the entity '{self.plural}';",
                    f"however the variable '{variable_name}' is defined for '{entity.plural}'.",
                    "Learn more about entities in our documentation:",
                    "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>.",
                ]
            )

            raise ValueError(message)
