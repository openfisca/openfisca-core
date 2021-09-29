import os
import textwrap
from typing import Any, Optional

from openfisca_core import commons
from openfisca_core.types import Descriptable, Representable
from openfisca_core.variables import Variable

from ._descriptors import VariableDescriptor


class Entity:
    """Represents an entity on which calculations can be run.

    For example an individual, a company, etc.

    Attributes:
        key (:obj:`str`): Key to identify the :class:`.Entity`.
        plural (:obj:`str`): The :attr:`key`, pluralised.
        label (:obj:`str`): A summary description.
        doc (:obj:`str`): A full description, dedented.
        is_person (:obj:`bool`): If is an individual, or not. Defaults to True.
        variable(:obj:`.VariableDescriotor`): To query for variables.

    Args:
        key: Key to identify the :class:`.Entity`.
        plural: ``key``, pluralised.
        label: A summary description.
        doc: A full description.

    Examples:
        >>> from openfisca_core.taxbenefitsystems import TaxBenefitSystem

        >>> entity = Entity(
        ...     "individual",
        ...     "individuals",
        ...     "An individual",
        ...     "The minimal legal entity on which a rule might be applied.",
        ...    )
        >>> entity
        <openfisca_core.entities.entity.Entity...

        >>> class Variable(Variable):
        ...     definition_period = "month"
        ...     value_type = float
        ...     entity = entity

        >>> tbs = TaxBenefitSystem([entity])
        >>> tbs.load_variable(Variable)
        <openfisca_core.entities.entity.Variable...

        >>> get_variable = tbs.get_variable
        >>> get_variable("Variable")
        <openfisca_core.entities.entity.Variable...

        >>> entity.variable = tbs.get_variable
        >>> entity.variable("Variable")
        <openfisca_core.entities.entity.Variable...

    """

    key: str
    plural: str
    label: str
    doc: str
    is_person: bool = True

    variable: Descriptable[Variable] = VariableDescriptor()
    """Queries :class:`.TaxBenefitSystem` to find a :class:`.Variable`.

    .. versionadded:: 35.5.0

    """

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.key = key
        self.plural = plural
        self.label = label
        self.doc = textwrap.dedent(doc)

    @commons.deprecated(since = "35.5.0", expires = "the future")
    def set_tax_benefit_system(self, tax_benefit_system: Representable) -> None:
        """Sets :attr:`.variable`.

        Args:
            tax_benefit_system: To query variables from.

        .. deprecated:: 35.5.0
            :meth:`.set_tax_benefit_system` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :attr:`.variable`.

        """

        self.variable = tax_benefit_system.get_variable

    @commons.deprecated(since = "35.5.0", expires = "the future")
    def check_role_validity(self, role: Any) -> None:
        """Checks if ``role`` is an instance of :class:`.Role`.

        Args:
            role: Any object.

        Returns:
            None.

        Raises:
            :exc:`ValueError`: When ``role`` is not a :class:`Role`.

        .. deprecated:: 35.5.0
            :meth:`.check_role_validity` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :func:`.entities.check_role_validity`.

        """

        from .helpers import check_role_validity

        return check_role_validity(role)

    @commons.deprecated(since = "35.5.0", expires = "the future")
    def get_variable(self, variable_name: str, check_existence: bool = False) -> Optional[Variable]:
        """Gets ``variable_name`` from :attr:`.variable`.

        Args:
            variable_name: The variable to be found.
            check_existence: Was the variable found? Defaults to False.

        Returns:
            :obj:`.Variable`: When the variable exists.
            None: When :attr:`.variable` is not defined.
            None: When the variable does't exist.

        Raises:
            :exc:`VariableNotFoundError`: When the variable doesn't exist and
                ``check_existence`` is True.

        .. seealso::
            Method :meth:`TaxBenefitSystem.get_variable`.

        .. versionchanged:: 35.5.0
            Now also returns None when :attr:`.variable` is not defined.

        .. deprecated:: 35.5.0
            :meth:`.get_variable` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :meth:`.variable`.

        """

        if self.variable is None:
            return None

        return self.variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name: str) -> None:
        """Checks if ``variable_name`` is defined for :obj:`.Entity`.

        Note:
            This should be extracted to a helper function.

        Args:
            variable_name: The :class:`.Variable` to be found.

        Returns:
            None: When :class:`.Variable` does not exist.
            None: When :class:`.Variable` exists, and its entity is ``self``.

        Raises:
            ValueError: When the :obj:`.Variable` exists but its :obj:`.Entity`
                is not ``self``.

        .. seealso::
            :class:`.Variable` and :attr:`.Variable.entity`.

        .. versionchanged:: 35.5.0
            Now also returns None when :class:`.Variable` is not found.

        .. versionchanged:: 35.5.0
            Now also returns None when :attr:`.variable` is not defined.

        """

        if self.variable is None:
            return None

        variable = self.variable(variable_name, check_existence = True)

        if variable is not None:
            variable_entity = variable.entity

            # Should be this:
            # if variable_entity is not self:
            if variable_entity.key != self.key:
                message = os.linesep.join([
                    "You tried to compute the variable '{0}' for the entity '{1}';".format(variable_name, self.plural),
                    "however the variable '{0}' is defined for '{1}'.".format(variable_name, variable_entity.plural),
                    "Learn more about entities in our documentation:",
                    "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
                raise ValueError(message)
