from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

import abc
import os

from . import types as t
from ._errors import TaxBenefitSystemUnsetError, VariableNotFoundError


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

    @property
    def variables(self, /) -> Mapping[t.VariableName, t.Variable]:
        """Get all variables defined for the entity.

        Returns:
            dict[str, Variable]: The variables defined for the entity.

        Raises:
            TaxBenefitSystemUnsetError: When the :attr:`.tax_benefit_system` is
                not set yet.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     periods,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> this = entities.SingleEntity("this", "these", "", "")
            >>> that = entities.SingleEntity("that", "those", "", "")

            >>> this.variables
            Traceback (most recent call last):
            TaxBenefitSystemUnsetError: The tax and benefit system is not se...

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([this, that])
            >>> this, that = tbs.entities

            >>> this.variables
            {}

            >>> that.variables
            {}

            >>> class tax(variables.Variable):
            ...     definition_period = periods.MONTH
            ...     value_type = float
            ...     entity = that

            >>> tbs.add_variable(tax)
            <openfisca_core.entities._core_entity.tax object at ...>

            >>> this.variables
            {}

            >>> that.variables
            {'tax': <openfisca_core.entities._core_entity.tax object at ...>}

        """
        if self.tax_benefit_system is None:
            raise TaxBenefitSystemUnsetError
        return {
            name: variable
            for name, variable in self.tax_benefit_system.variables.items()
            if variable.entity.key == self.key
        }

    def get_variable(
        self,
        variable_name: t.VariableName,
        check_existence: bool = False,
    ) -> None | t.Variable:
        """Get ``variable_name`` from ``variables``.

        Args:
            variable_name: The ``Variable`` to be found.
            check_existence: Was the ``Variable`` found?

        Returns:
            Variable: When the ``Variable`` exists.
            None: When the ``Variable`` doesn't exist.

        Raises:
            TaxBenefitSystemUnsetError: When the :attr:`.tax_benefit_system` is
                not set yet.
            VariableNotFoundError: When ``check_existence`` is ``True`` and the
                ``Variable`` doesn't exist.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     periods,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> this = entities.SingleEntity("this", "these", "", "")
            >>> that = entities.SingleEntity("that", "those", "", "")

            >>> this.get_variable("tax")
            Traceback (most recent call last):
            TaxBenefitSystemUnsetError: The tax and benefit system is not se...

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([this, that])
            >>> this, that = tbs.entities

            >>> this.get_variable("tax")

            >>> this.get_variable("tax", check_existence=True)
            Traceback (most recent call last):
            VariableNotFoundError: You requested the variable 'tax', but it ...

            >>> class tax(variables.Variable):
            ...     definition_period = periods.MONTH
            ...     value_type = float
            ...     entity = that

            >>> tbs.add_variable(tax)
            <openfisca_core.entities._core_entity.tax object at ...>

            >>> this.get_variable("tax")

            >>> that.get_variable("tax")
            <openfisca_core.entities._core_entity.tax object at ...>

        """
        if self.tax_benefit_system is None:
            raise TaxBenefitSystemUnsetError
        if not check_existence:
            return self.variables.get(variable_name)
        try:
            return self.variables[variable_name]
        except KeyError as error:
            raise VariableNotFoundError(variable_name, self.plural) from error

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
