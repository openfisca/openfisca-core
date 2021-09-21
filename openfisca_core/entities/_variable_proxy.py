from __future__ import annotations

import functools
import os
from typing import Any, Optional, Type

from typing_extensions import Protocol

from openfisca_core.types import HasPlural, HasVariables, SupportsFormula

DOC_URL = "https://openfisca.org/doc/coding-the-legislation"

E = HasPlural
T = HasVariables
V = SupportsFormula


class Query(Protocol):
    """A dummy class to "duck-check" :meth:`.TaxBenefitSystem.get_variable`."""

    def __call__(
            self,
            __arg1: str,
            __arg2: bool = False,
            ) -> Optional["VariableProxy"]:
        """See comment above."""

        ...


class VariableProxy:
    """A `descriptor`_ to find an :obj:`.Entity`'s :obj:`.Variable`.

    Attributes:
        entity (:obj:`.Entity`, optional):
            The :obj:`.Entity` ``owner`` of the descriptor.
        tax_benefit_system (:obj:`.TaxBenefitSystem`, optional):
            The :obj:`.Entity`'s :obj:`.TaxBenefitSystem`.
        query (:meth:`.TaxBenefitSystem.get_variable`):
            The method used to query the :obj:`.TaxBenefitSystem`.

    Examples:
        >>> from openfisca_core.entities import Entity
        >>> from openfisca_core.taxbenefitsystems import TaxBenefitSystem
        >>> from openfisca_core.variables import Variable

        >>> entity = Entity(
        ...     "individual",
        ...     "individuals",
        ...     "An individual",
        ...     "The minimal legal entity on which a rule can be applied.",
        ...    )

        >>> class Variable(Variable):
        ...     definition_period = "month"
        ...     value_type = float
        ...     entity = entity

        >>> tbs = TaxBenefitSystem([entity])
        >>> tbs.add_variable(Variable)
        <openfisca_core.entities._variable_proxy.Variable...

        >>> entity.tax_benefit_system = tbs

        >>> entity.variables.get("Variable")
        <...Variable...

        >>> entity.variables.exists().get("Variable")
        <...Variable...

        >>> entity.variables.isdefined().get("Variable")
        <...Variable...

    .. _descriptor: https://docs.python.org/3/howto/descriptor.html

    .. versionadded:: 35.7.0

    """

    entity: Optional[E] = None
    tax_benefit_system: Optional[T] = None
    query: Query

    def __get__(self, entity: E, type: Type[E]) -> Optional[VariableProxy]:
        """Binds :meth:`.TaxBenefitSystem.get_variable`."""

        self.entity = entity

        self.tax_benefit_system = getattr(
            self.entity,
            "tax_benefit_system",
            None,
            )

        if self.tax_benefit_system is None:
            return None

        self.query = self.tax_benefit_system.get_variable

        return self

    def __set__(self, entity: E, value: Any) -> None:
        NotImplemented

    def get(self, variable_name: str) -> Optional[V]:
        """Runs the query for ``variable_name``, based on the options given.

        Args:
            variable_name: The :obj:`.Variable` to be found.

        Returns:
            :obj:`.Variable` or :obj:`None`:
            :obj:`.Variable` when the :obj:`.Variable` exists.
            :obj:`None` when the :attr:`.tax_benefit_system` is not set.

        Raises:
            :exc:`.VariableNotFoundError`: When :obj:`.Variable` doesn't exist.
            :exc:`.ValueError`: When the :obj:`.Variable` exists but is defined
            for another :obj:`.Entity`.

        .. versionadded:: 35.7.0

        """

        if self.entity is None:
            return NotImplemented

        return self.query(variable_name)

    def exists(self) -> VariableProxy:
        """Sets ``check_existence`` to ``True``."""

        self.query = functools.partial(
            self.query,
            check_existence = True,
            )

        return self

    def isdefined(self) -> VariableProxy:
        """Checks that ``variable_name`` is defined for :attr:`.entity`."""

        # We assume that we're also checking for existance.
        self.exists()

        self.query = functools.partial(
            self._isdefined,
            self.query,
            )

        return self

    def _isdefined(self, query: Query, variable_name: str, **any: Any) -> Any:
        variable = query(variable_name)

        if self.entity is None:
            return None

        if variable is None:
            return None

        if variable.entity is None:
            return None

        if self.entity != variable.entity:
            message = os.linesep.join([
                f"You tried to compute the variable '{variable_name}' for",
                f"the entity '{self.entity.plural}'; however the variable",
                f"'{variable_name}' is defined for the entity",
                f"'{variable.entity.plural}'. Learn more about entities",
                f"in our documentation: <{DOC_URL}/50_entities.html>.",
                ])

            raise ValueError(message)

        return variable
