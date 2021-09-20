import dataclasses
import textwrap
from typing import Any, Iterator, Optional, Tuple

from openfisca_core.commons import deprecated
from openfisca_core.types import Descriptable, Modellable, Representable

from .. import entities
from ._variable_proxy import VariableProxy


@dataclasses.dataclass
class Entity:
    """Represents an entity on which calculations can be run.

    For example an individual, a company, etc. An :class:`.Entity`
    represents an "abstract" atomic unit of the legislation, as in
    "any individual", or "any company".

    Attributes:
        key (:obj:`str`):
            Key to identify the :class:`.Entity`.
        plural (:obj:`str`):
            The ``key``, pluralised.
        label (:obj:`str`):
            A summary description.
        doc (:obj:`str`):
            A full description, dedented.
        is_person (:obj:`bool`):
            Represents an individual? Defaults to True.
        populations (:class:`.Population`):
            An :class:`.Entity` has many :class:`Populations <.Population>`,
            that is a concrete case of an :class:`.Entity` —a dataset, a
            survey, a single individual case…
        variables (:class:`.Variable`):
            An :class:`.Entity` has many :class:`Variables <.Variable>`. In
            fact, each :class:`.Variable` is defined for a specific
            :class:`.Entity`.

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
        ...     "The minimal legal entity on which a rule might be applied.",
        ...    )

        >>> repr(Entity)
        "<class 'openfisca_core.entities.entity.Entity'>"

        >>> repr(entity)
        '<Entity(individual)>'

        >>> str(entity)
        'individuals'

        >>> dict(entity)
        {'key': 'individual', 'plural': 'individuals', 'label': 'An individ...}

        >>> list(entity)
        [('key', 'individual'), ('plural', 'individuals'), ('label', 'An in...]

        >>> entity == entity
        True

        >>> entity != entity
        False

        >>> from openfisca_core.taxbenefitsystems import TaxBenefitSystem
        >>> from openfisca_core.variables import Variable

        >>> class Variable(Variable):
        ...     definition_period = "month"
        ...     value_type = float
        ...     entity = entity

        >>> tbs = TaxBenefitSystem([entity])
        >>> tbs.add_variable(Variable)
        <openfisca_core.entities.entity.Variable...

        >>> entity.tax_benefit_system = tbs

        >>> entity.variables.get("Variable")
        <...Variable...

        >>> entity.variables.exists().get("Variable")
        <...Variable...

        >>> entity.variables.isdefined().get("Variable")
        <...Variable...

    .. versionchanged:: 35.7.0
        Hereafter ``variables`` allows querying a :obj:`.TaxBenefitSystem`
        for a :obj:`.Variable`.

    .. versionchanged:: 35.7.0
        Hereafter the equality of an :obj:`.Entity` is determined by its
        data attributes.

    """

    key: str
    plural: str
    label: str
    doc: str

    variables: Descriptable[VariableProxy] = dataclasses.field(
        init = False,
        compare = False,
        default = VariableProxy(),
        )
    """:obj:`.Variables`: A descriptor to search for a :obj:`.Variable`."""

    @property
    def tax_benefit_system(self) -> Optional[Representable]:
        """An :obj:`.Entity`'s :obj:`.TaxBenefitSystem`."""

        return self._tax_benefit_system

    @tax_benefit_system.setter
    def tax_benefit_system(self, value: Representable) -> None:
        self._tax_benefit_system = value

    def __post_init__(self) -> None:
        self.doc = textwrap.dedent(self.doc)
        self.is_person = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.key})>"

    def __str__(self) -> str:
        return self.plural

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        return (item for item in self.__dict__.items())

    @deprecated(since = "35.7.0", expires = "the future")
    def set_tax_benefit_system(
            self,
            tax_benefit_system: Representable,
            ) -> None:
        """Sets ``_tax_benefit_system``.

        Args:
            tax_benefit_system: To query variables from.

        .. deprecated:: 35.7.0
            :meth:`.set_tax_benefit_system` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :attr:`.tax_benefit_system`.

        """

        self.tax_benefit_system = tax_benefit_system

    @deprecated(since = "35.7.0", expires = "the future")
    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = False,
            ) -> Optional[Modellable]:
        """Gets ``variable_name`` from ``variables``.

        Args:
            variable_name: The variable to be found.
            check_existence: Was the variable found? Defaults to False.

        Returns:
            :obj:`.Variable` or :obj:`None`:
            :obj:`.Variable` when the :obj:`.Variable` exists.
            :obj:`None` when the :obj:`.Variable` doesn't exist.

        Raises:
            :exc:`.VariableNotFoundError`: When ``check_existence`` is True and the
            :obj:`.Variable` doesn't exist.

        .. deprecated:: 35.7.0
            :meth:`.get_variable` has been deprecated and will be
            removed in the future. The functionality is now provided by
            ``variables``.

        """

        if self.variables is None:
            return None

        if check_existence:
            return self.variables.exists().get(variable_name)

        return self.variables.get(variable_name)

    @deprecated(since = "35.7.0", expires = "the future")
    def check_variable_defined_for_entity(
            self,
            variable_name: str,
            ) -> Optional[Modellable]:
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

        .. deprecated:: 35.7.0
            :meth:`.check_variable_defined_for_entity` has been deprecated and
            will be removed in the future. The functionality is now provided by
            ``variables``.

        """

        if self.variables is None:
            return None

        return self.variables.isdefined().get(variable_name)

    @staticmethod
    @deprecated(since = "35.7.0", expires = "the future")
    def check_role_validity(role: Any) -> None:
        """Checks if ``role`` is an instance of :class:`.Role`.

        Args:
            role: Any object.

        Returns:
            :obj:`None`.

        .. deprecated:: 35.7.0
            :meth:`.check_role_validity` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :func:`.entities.check_role_validity`.

        """

        return entities.check_role_validity(role)
