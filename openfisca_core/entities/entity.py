from __future__ import annotations

from typing import Any, Optional
from openfisca_core.typing import (
    RoleProtocol,
    TaxBenefitSystemProtocol,
    VariableProtocol,
    )

import dataclasses
import textwrap

from ._variable_proxy import _VariableProxy


@dataclasses.dataclass
class Entity:
    """Represents an entity on which calculations can be run.

    For example an individual, a company, etc. An :class:`.Entity`
    represents an "abstract" atomic unit of the legislation, as in
    "any individual", or "any company".

    Attributes:
        key: Key to identify the :class:`.Entity`.
        plural: The ``key``, pluralised.
        label: A summary description.
        doc: A full description, dedented.
        is_person: Represents an individual. Defaults to True.

    Args:
        key: Key to identify the :class:`.Entity`.
        plural: ``key``, pluralised.
        label: A summary description.
        doc: A full description.

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
        'individuals'

    .. versionchanged:: 35.8.0
        Added documentation, doctests, and typing.

    """

    __slots__ = tuple((
        "_tax_benefit_system",
        "doc",
        "is_person",
        "key",
        "label",
        "plural",
        ))

    key: str
    plural: str
    label: str
    doc: str
    is_person: bool
    _variables: _VariableProxy = dataclasses.field(
        init = False,
        compare = False,
        default = _VariableProxy(),
        )

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.key = key
        self.label = label
        self.plural = plural
        self.doc = textwrap.dedent(doc)
        self.is_person = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def __str__(self) -> str:
        return self.plural

    @property
    def tax_benefit_system(self) -> Optional[TaxBenefitSystemProtocol]:
        """An :obj:`.Entity` belongs to a :obj:`.TaxBenefitSystem`."""

        return self._tax_benefit_system

    @tax_benefit_system.setter
    def tax_benefit_system(self, value: TaxBenefitSystemProtocol) -> None:
        self._tax_benefit_system = value

    def set_tax_benefit_system(
            self,
            tax_benefit_system: TaxBenefitSystemProtocol,
            ) -> None:
        """Sets ``_tax_benefit_system``.

        Args:
            tax_benefit_system: To query variables from.

        .. deprecated:: 35.8.0
            :meth:`.set_tax_benefit_system` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :attr:`.tax_benefit_system`.

        """

        self.tax_benefit_system = tax_benefit_system

    @property
    def variables(self) -> Optional[_VariableProxy]:
        """An :class:`.Entity` has many :class:`Variables <.Variable>`."""

        return self._variables

    @staticmethod
    def check_role_validity(role: Any) -> None:
        """Checks if ``role`` is an instance of :class:`.Role`.

        Args:
            role: Any object.

        Raises:
            ValueError: When ``role`` is not a :class:`.Role`.

        .. deprecated:: 35.8.0
            :meth:`.check_role_validity` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :func:`.entities.check_role_validity`.

        """

        if role is not None and not isinstance(role, RoleProtocol):
            raise ValueError(f"{role} is not a valid role")

    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = False,
            ) -> Optional[VariableProtocol]:
        """Gets ``variable_name`` from ``variables``.

        Args:
            variable_name: The variable to be found.
            check_existence: Was the variable found? Defaults to False.

        Returns:
            :obj:`.Variable` or :obj:`None`:
            :obj:`.Variable` when the :obj:`.Variable` exists.
            :obj:`None` when the :obj:`.Variable` doesn't exist.

        Raises:
            :exc:`.VariableNotFoundError`: When ``check_existence`` is True and
            the :obj:`.Variable` doesn't exist.

        Examples:
            >>> from openfisca_core.taxbenefitsystems import TaxBenefitSystem
            >>> from openfisca_core.variables import Variable

            >>> this = Entity("this", "", "", "")
            >>> that = Entity("that", "", "", "")

            >>> this.get_variable("foo")

            >>> this.get_variable("foo", check_existence = True)

            >>> this.tax_benefit_system = TaxBenefitSystem([that])

            >>> this.get_variable("foo")

            >>> this.get_variable("foo", check_existence = True)
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class foo(Variable):
            ...     definition_period = "month"
            ...     value_type = float
            ...     entity = that

            >>> this.tax_benefit_system.add_variable(foo)
            <openfisca_core.entities.entity.foo object at ...>

            >>> this.get_variable("foo")
            <openfisca_core.entities.entity.foo object at ...>

        .. versionchanged:: 35.8.0
            Added documentation, doctests, and typing.

        """

        if self.variables is None:
            return None

        if check_existence:
            return self.variables.exists().get(variable_name)

        return self.variables.get(variable_name)

    def check_variable_defined_for_entity(
            self,
            variable_name: str,
            ) -> Optional[VariableProtocol]:
        """Checks if ``variable_name`` is defined for ``self``.

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

        Examples:
            >>> from openfisca_core.taxbenefitsystems import TaxBenefitSystem
            >>> from openfisca_core.variables import Variable

            >>> this = Entity("this", "", "", "")
            >>> that = Entity("that", "", "", "")

            >>> this.check_variable_defined_for_entity("foo")

            >>> this.tax_benefit_system = TaxBenefitSystem([that])
            >>> this.check_variable_defined_for_entity("foo")
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value...

            >>> class foo(Variable):
            ...     definition_period = "month"
            ...     value_type = float
            ...     entity = that

            >>> this.tax_benefit_system.add_variable(foo)
            <openfisca_core.entities.entity.foo object at ...>

            >>> this.check_variable_defined_for_entity("foo")
            Traceback (most recent call last):
            ValueError: You tried to compute the variable 'foo' for the enti...

            >>> foo.entity = this
            >>> this.tax_benefit_system.update_variable(foo)
            <openfisca_core.entities.entity.foo object at ...>

            >>> this.check_variable_defined_for_entity("foo")
            <openfisca_core.entities.entity.foo object at ...>

        .. versionchanged:: 35.8.0
            Added documentation, doctests, and typing.

        """

        if self.variables is None:
            return None

        return self.variables.isdefined().get(variable_name)
