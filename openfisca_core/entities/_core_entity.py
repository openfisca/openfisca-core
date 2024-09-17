from __future__ import annotations

import os
from abc import abstractmethod

from . import types as t
from .role import Role


class _CoreEntity:
    """Base class to build entities from."""

    #: A key to identify the entity.
    key: t.EntityKey
    #: The ``key``, pluralised.
    plural: t.EntityPlural | None

    #: A summary description.
    label: str | None

    #: A full description.
    doc: str | None

    #: Whether the entity is a person or not.
    is_person: bool

    #: A TaxBenefitSystem instance.
    _tax_benefit_system: t.TaxBenefitSystem | None = None

    @abstractmethod
    def __init__(
        self, key: str, plural: str, label: str, doc: str, *args: object
    ) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def set_tax_benefit_system(self, tax_benefit_system: t.TaxBenefitSystem) -> None:
        """An Entity belongs to a TaxBenefitSystem."""
        self._tax_benefit_system = tax_benefit_system

    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> t.Variable | None:
        """Get a ``variable_name`` from ``variables``."""
        if self._tax_benefit_system is None:
            raise ValueError(
                "You must set 'tax_benefit_system' before calling this method."
            )
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name: str) -> None:
        """Check if ``variable_name`` is defined for ``self``."""
        variable: t.Variable | None
        entity: t.CoreEntity

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

    def check_role_validity(self, role: object) -> None:
        """Check if a ``role`` is an instance of Role."""
        if role is not None and not isinstance(role, Role):
            raise ValueError(f"{role} is not a valid role")
