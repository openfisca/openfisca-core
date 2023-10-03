from __future__ import annotations

from openfisca_core.types import TaxBenefitSystem, Variable
from typing import Any, Optional

import os

from ._description import Description
from .role import Role


class Entity:
    """
    Represents an entity (e.g. a person, a household, etc.) on which calculations can be run.
    """

    #: A description of the Entity.
    description: Description

    @property
    def key(self) -> str:
        """A key to identify the Entity."""
        return self.description.key

    @property
    def plural(self) -> str | None:
        """The ``key``, pluralised."""
        return self.description.plural

    @property
    def label(self) -> str | None:
        """A summary description."""
        return self.description.label

    @property
    def doc(self) -> str | None:
        """A full description, non-indented."""
        return self.description.doc

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.description = Description(key, plural, label, doc)
        self.is_person = True
        self._tax_benefit_system = None

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

        if entity.key != self.key:
            message = (
                f"You tried to compute the variable '{variable_name}' for",
                f"the entity '{self.plural}'; however the variable",
                f"'{variable_name}' is defined for '{entity.plural}'.",
                "Learn more about entities in our documentation:",
                "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>.",
            )
            raise ValueError(os.linesep.join(message))
