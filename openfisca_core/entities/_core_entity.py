from __future__ import annotations

from typing import ClassVar

import abc
import os

from . import types as t


class CoreEntity:
    """Base class to build entities from.

    Args:
        *__args: Any arguments.
        **__kwargs: Any keyword arguments.

    Examples:
        >>> from openfisca_core import entities
        >>> from openfisca_core.entities import types as t

        >>> class Entity(entities.CoreEntity):
        ...     def __init__(self, key):
        ...         self.key = t.EntityKey(key)

        >>> Entity("individual")
        Entity(individual)

    """

    #: A key to identify the ``CoreEntity``.
    key: t.EntityKey

    #: The ``key`` pluralised.
    plural: t.EntityPlural

    #: A summary description.
    label: str

    #: A full description.
    doc: str

    #: Whether the ``CoreEntity`` is a person or not.
    is_person: ClassVar[bool]

    #: A ``TaxBenefitSystem`` instance.
    tax_benefit_system: None | t.TaxBenefitSystem = None

    @abc.abstractmethod
    def __init__(self, *__args: object, **__kwargs: object) -> None: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

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

            >>> this = entities.SingleEntity("this", "", "", "")
            >>> that = entities.SingleEntity("that", "", "", "")

            >>> this.get_variable("tax")
            Traceback (most recent call last):
            ValueError: You must set 'tax_benefit_system' before calling this...

            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem([this])
            >>> this.tax_benefit_system = tax_benefit_system

            >>> this.get_variable("tax")

            >>> this.get_variable("tax", check_existence=True)
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class tax(variables.Variable):
            ...     definition_period = periods.MONTH
            ...     value_type = float
            ...     entity = that

            >>> this.tax_benefit_system.add_variable(tax)
            <openfisca_core.entities._core_entity.tax object at ...>

            >>> this.get_variable("tax")
            <openfisca_core.entities._core_entity.tax object at ...>


        """
        if self.tax_benefit_system is None:
            msg = "You must set 'tax_benefit_system' to call this method."
            raise ValueError(msg)
        return self.tax_benefit_system.get_variable(variable_name, check_existence)

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

            >>> this = entities.SingleEntity("this", "", "", "")
            >>> that = entities.SingleEntity("that", "", "", "")
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem([that])
            >>> this.tax_benefit_system = tax_benefit_system

            >>> this.check_variable_defined_for_entity("tax")
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class tax(variables.Variable):
            ...     definition_period = periods.WEEK
            ...     value_type = int
            ...     entity = that

            >>> this.tax_benefit_system.add_variable(tax)
            <openfisca_core.entities._core_entity.tax object at ...>

            >>> this.check_variable_defined_for_entity("tax")
            Traceback (most recent call last):
            ValueError: You tried to compute the variable 'tax' for the enti...

            >>> tax.entity = this

            >>> this.tax_benefit_system.update_variable(tax)
            <openfisca_core.entities._core_entity.tax object at ...>

            >>> this.check_variable_defined_for_entity("tax")

        """
        entity: None | t.CoreEntity = None
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


__all__ = ["CoreEntity"]
