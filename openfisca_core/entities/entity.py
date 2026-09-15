from __future__ import annotations

from typing import ClassVar

import textwrap
import os
from itertools import chain

from . import types as t
from .role import Role


class Relationship:
    def __init__(self, a: Entity, b: Entity, role_descriptions: Sequence[t.RoleParams]):
        self.a: Entity = a
        self.b: Entity = b
        self.role_descriptions: Sequence[t.RoleParams] = role_descriptions
        roles = []
        for role_description in role_descriptions:
            role = Role(role_description, self)
            setattr(a, role.key.upper(), role)
            roles.append(role)
            if subroles := role_description.get("subroles"):
                role.subroles = ()
                for subrole_key in subroles:
                    subrole = Role({"key": subrole_key, "max": 1}, self)
                    setattr(a, subrole.key.upper(), subrole)
                    role.subroles = (*role.subroles, subrole)
                role.max = len(role.subroles)
        self.roles: Iterable[Role] = roles



class Entity:
    """Base class to build entities from.

    Args:
        *__args: Any arguments.
        **__kwargs: Any keyword arguments.

    Examples:
        >>> from openfisca_core.entities import types as t

        >>> Entity("individual", "individuals", "Individual", "")
        Entity(individual)

    """

    #: A key to identify the ``Entity``.
    key: t.EntityKey

    #: The ``key`` pluralised.
    plural: t.EntityPlural

    #: A summary description.
    label: str

    #: A full description.
    doc: str

    #: A ``TaxBenefitSystem`` instance.
    _tax_benefit_system: None | t.TaxBenefitSystem = None

    def __init__(self, key: str, plural: str, label: str, doc: str = "") -> None:
        self.key = t.EntityKey(key)
        self.plural = t.EntityPlural(plural)
        self.label = label
        self.doc = textwrap.dedent(doc)
        self.relationships = []
        self.flattened_roles = []


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def set_tax_benefit_system(self, tax_benefit_system: t.TaxBenefitSystem) -> None:
        """An ``Entity`` belongs to a ``TaxBenefitSystem``."""
        self._tax_benefit_system = tax_benefit_system

    def get_variable(
        self,
        variable_name: t.VariableName,
        check_existence: bool = False,
    ) -> t.Variable | None:
        """Get ``variable_name`` from ``variables``.

        Args:
            variable_name: The ``Variable`` to be found.
            check_existence: Was the ``Variable`` found?

        Returns:
            Variable: When the ``Variable`` exists.
            None: When the ``Variable`` doesn't exist.

        Raises:
            ValueError: When the :attr:`_tax_benefit_system` is not set yet.
            ValueError: When ``check_existence`` is ``True`` and
                the ``Variable`` doesn't exist.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     periods,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> this = entities.Entity("this", "", "")
            >>> that = entities.Entity("that", "", "")

            >>> this.get_variable("tax")
            Traceback (most recent call last):
            ValueError: You must set 'tax_benefit_system' before calling this...

            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem([this])
            >>> this.set_tax_benefit_system(tax_benefit_system)

            >>> this.get_variable("tax")

            >>> this.get_variable("tax", check_existence=True)
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class tax(variables.Variable):
            ...     definition_period = periods.MONTH
            ...     value_type = float
            ...     entity = that

            >>> this._tax_benefit_system.add_variable(tax)
            <openfisca_core.entities.entity.tax object at ...>

            >>> this.get_variable("tax")
            <openfisca_core.entities.entity.tax object at ...>


        """
        if self._tax_benefit_system is None:
            msg = "You must set 'tax_benefit_system' before calling this method."
            raise ValueError(
                msg,
            )
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name: t.VariableName) -> None:
        """Check if ``variable_name`` is defined for ``self``.

        Args:
            variable_name: The ``Variable`` to be found.

        Raises:
            ValueError: When the ``Variable`` exists but is defined
                for another ``Entity``.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     periods,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> this = entities.Entity("this", "", "")
            >>> that = entities.Entity("that", "", "")
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem([that])
            >>> this.set_tax_benefit_system(tax_benefit_system)

            >>> this.check_variable_defined_for_entity("tax")
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class tax(variables.Variable):
            ...     definition_period = periods.WEEK
            ...     value_type = int
            ...     entity = that

            >>> this._tax_benefit_system.add_variable(tax)
            <openfisca_core.entities.entity.tax object at ...>

            >>> this.check_variable_defined_for_entity("tax")
            Traceback (most recent call last):
            ValueError: You tried to compute the variable 'tax' for the enti...

            >>> tax.entity = this

            >>> this._tax_benefit_system.update_variable(tax)
            <openfisca_core.entities.entity.tax object at ...>

            >>> this.check_variable_defined_for_entity("tax")

        """
        entity: None | t.Entity = None
        variable: None | t.Variable = self.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is not None:
            entity = variable.entity

        if entity is None:
            return

        if entity.key != self.key:
            message = (
                f"You tried to compute the variable '{variable_name}' for",
                f"the entity '{self.plural}'; however the variable",
                f"'{variable_name}' is defined for '{entity.plural}'.",
                "Learn more about entities in our documentation:",
                "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>.",
            )
            raise ValueError(os.linesep.join(message))

    @staticmethod
    def check_role_validity(role: object) -> None:
        """Check if ``role`` is an instance of  ``Role``.

        Args:
            role: Any object.

        Raises:
            ValueError: When ``role`` is not a ``Role``.

        Examples:
            >>> from openfisca_core import entities

            >>> role = entities.Role({"key": "key"}, object())
            >>> entities.check_role_validity(role)

            >>> entities.check_role_validity("hey!")
            Traceback (most recent call last):
            ValueError: hey! is not a valid role

        """
        if role is not None and not isinstance(role, Role):
            msg = f"{role} is not a valid role"
            raise ValueError(msg)


    def add_relationship(self, entity: Entity, role_descriptions: Sequence[t.RoleParams]):
        relationship = Relationship(self, entity, role_descriptions)
        self.relationships.append(relationship)
        entity.relationships.append(relationship)
        self.flattened_roles = tuple(*self.flattened_roles,
            chain.from_iterable(role.subroles or [role] for role in relationship.roles),
        )

__all__ = ["Entity"]
