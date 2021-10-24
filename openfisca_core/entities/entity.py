from __future__ import annotations

from typing import Any, Optional

import os
import textwrap
from dataclasses import dataclass

from openfisca_core.types import HasVariables

from .. import entities


@dataclass
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
        ...     "The minimal legal entity on which a rule might be applied.",
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
        "key",
        "plural",
        "label",
        "doc",
        "is_person",
        "_tax_benefit_system",
        ))

    key: str
    plural: str
    label: str
    doc: str

    def __post_init__(self, *_args: Any) -> None:
        self.doc = textwrap.dedent(self.doc)
        self.is_person = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def __str__(self) -> str:
        return self.plural

    @property
    def tax_benefit_system(self) -> Optional[HasVariables]:
        """An :obj:`.Entity` belongs to a :obj:`.TaxBenefitSystem`."""

        return self._tax_benefit_system

    @tax_benefit_system.setter
    def tax_benefit_system(self, value: HasVariables) -> None:
        self._tax_benefit_system = value

    def set_tax_benefit_system(self, tax_benefit_system: HasVariables) -> None:
        """Sets ``_tax_benefit_system``.

        Args:
            tax_benefit_system: To query variables from.

        .. deprecated:: 35.8.0
            :meth:`.set_tax_benefit_system` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :attr:`.tax_benefit_system`.

        """

        self.tax_benefit_system = tax_benefit_system

    @staticmethod
    def check_role_validity(role: Any) -> None:
        """Checks if ``role`` is an instance of :class:`.Role`.

        Args:
            role: Any object.

        Returns:
            None.

        .. deprecated:: 35.8.0
            :meth:`.check_role_validity` has been deprecated and will be
            removed in the future. The functionality is now provided by
            :func:`.entities.check_role_validity`.

        """

        return entities.check_role_validity(role)

    def get_variable(self, variable_name, check_existence = False):
        return self._tax_benefit_system.get_variable(variable_name, check_existence)

    def check_variable_defined_for_entity(self, variable_name):
        variable_entity = self.get_variable(variable_name, check_existence = True).entity
        # Should be this:
        # if variable_entity is not self:
        if variable_entity.key != self.key:
            message = os.linesep.join([
                "You tried to compute the variable '{0}' for the entity '{1}';".format(variable_name, self.plural),
                "however the variable '{0}' is defined for '{1}'.".format(variable_name, variable_entity.plural),
                "Learn more about entities in our documentation:",
                "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
            raise ValueError(message)
