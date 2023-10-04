from __future__ import annotations

from openfisca_core.types import TaxBenefitSystem, Variable
from typing import Any, Optional

import os

from ._description import Description
from ._subrole import SubRole
from .role import Role


class Entity:
    """Represents an entity on which calculations can be run.

    For example an individual, a company, etc. An :class:`.Entity`
    represents an "abstract" atomic unit of the legislation, as in
    "any individual", or "any company".

    Attributes:
        description (Description): A description of the Entity.
        is_person (bool): Represents an individual? Defaults to True.

    Args:
        key (str): Key to identify the Entity.
        plural (str): ``key``, pluralised.
        label (str): A summary description.
        doc (str): A full description.

    Examples:
        >>> entity = Entity(
        ...     "individual",
        ...     "individuals",
        ...     "An individual",
        ...     "\t\t\tThe minimal legal entity on which a rule might be a...",
        ...    )

        >>> repr(Entity)
        "<class 'openfisca_core.entities.entity.Entity'>"

        >>> repr(entity)
        'Entity(individual)'

        >>> str(entity)
        'Entity(individual)'

        >>> {entity}
        {Entity(individual)}

    """

    #: A description of the Entity.
    description: Description

    #: Whether it represents an individual or not.
    is_person: bool = True

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

    def set_tax_benefit_system(self, tax_benefit_system: TaxBenefitSystem) -> None:
        self._tax_benefit_system = tax_benefit_system

    @staticmethod
    def check_role_validity(role: Any) -> None:
        if role is None:
            return None

        if not isinstance(role, (Role, SubRole)):
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"
