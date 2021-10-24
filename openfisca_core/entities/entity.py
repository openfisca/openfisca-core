from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass

from openfisca_core.entities import Role


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
        '<Entity(individual)>'

        >>> str(entity)
        'individuals'

    .. versionchanged:: 35.7.0
        * Added documentation, doctests, and typing.
        * Transformed into a :func:`dataclasses.dataclass`.
        * Added :attr:`object.__slots__` to improve performance.

    """

    def __init__(self, key, plural, label, doc):
        self.key = key
        self.label = label
        self.plural = plural
        self.doc = textwrap.dedent(doc)
        self.is_person = True
        self._tax_benefit_system = None

    def set_tax_benefit_system(self, tax_benefit_system):
        self._tax_benefit_system = tax_benefit_system

    def check_role_validity(self, role):
        if role is not None and not type(role) == Role:
            raise ValueError("{} is not a valid role".format(role))

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
