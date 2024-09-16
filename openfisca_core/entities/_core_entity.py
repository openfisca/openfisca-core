from __future__ import annotations

from typing import Any

from openfisca_core.types import TaxBenefitSystem, Variable

import os
from abc import abstractmethod

from .role import Role
from .types import Entity


class _CoreEntity:
    """Base class to build entities from."""

    #: A key to identify the entity.
    key: str

    #: The ``key``, pluralised.
    plural: str | None

    #: A summary description.
    label: str | None

    #: A full description.
    doc: str | None

    #: Whether the entity is a person or not.
    is_person: bool

    #: A TaxBenefitSystem instance.
    _tax_benefit_system: TaxBenefitSystem | None = None

    @abstractmethod
    def __init__(self, key: str, plural: str, label: str, doc: str, *args: Any) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def set_tax_benefit_system(self, tax_benefit_system: TaxBenefitSystem) -> None:
        """An Entity belongs to a TaxBenefitSystem."""
        self._tax_benefit_system = tax_benefit_system

    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> Variable | None:
        """Get a ``variable_name`` from ``variables``."""
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name: str) -> None:
        """Check if ``variable_name`` is defined for ``self``."""
        variable: Variable | None
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

    def check_role_validity(self, role: Any) -> None:
        """Check if a ``role`` is an instance of Role."""
        if role is not None and not isinstance(role, Role):
            raise ValueError(f"{role} is not a valid role")
