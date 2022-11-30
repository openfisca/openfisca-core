"""Domain-model.

The domain-model is composed of structures meant to encapsulate data in a way
that is unique to the context. Therefore, their identity is not equivalent to
the sum of their properties. If two data objects hold the same identifier, even
if the data they hold is different, they are equal but not fungible.

Examples:
    If we take entities, they are equal as long as they share the same ``key``.
    Let's take the following example:

    >>> from openfisca_core import entities

    >>> this = entities.Entity(1, "a", "b", "c")
    >>> that = entities.Entity(1, "d", "f", "g")
    >>> this == that
    True

    As you can see, ``this`` and ``that`` are equal because they share the same
    ``key``:

    >>> this.key == that.key
    True

    The opposite is also true:

    >>> that = entities.Entity(2, "a", "b", "c")
    >>> this == that
    False

    >>> this.key == that.key
    False

"""

from __future__ import annotations

import numpy
import typing_extensions
from typing import Any, Optional
from typing_extensions import Protocol

import abc


class Entity(Protocol):
    """Entity protocol."""

    key: Any
    plural: Any

    @abc.abstractmethod
    def check_role_validity(self, role: Any) -> None:
        """Abstract method."""

    @abc.abstractmethod
    def check_variable_defined_for_entity(self, variable_name: Any) -> None:
        """Abstract method."""

    @abc.abstractmethod
    def get_variable(
            self, variable_name: Any,
            check_existence: Any = ...,
            ) -> Optional[Any]:
        """Abstract method."""


class Formula(Protocol):
    """Formula protocol."""

    @abc.abstractmethod
    def __call__(
            self,
            population: Population,
            instant: Any,
            params: Params,
            ) -> numpy.ndarray:
        """Abstract method."""


class Holder(Protocol):
    """Holder protocol."""

    @abc.abstractmethod
    def clone(self, population: Any) -> Holder:
        """Abstract method."""

    @abc.abstractmethod
    def get_memory_usage(self) -> Any:
        """Abstract method."""


@typing_extensions.runtime_checkable
class ParameterNodeAtInstant(Protocol):
    """ParameterNodeAtInstant protocol."""


class Params(Protocol):
    """Params protocol."""

    @abc.abstractmethod
    def __call__(self, instant: Any) -> ParameterNodeAtInstant:
        """Abstract method."""


class Population(Protocol):
    """Population protocol."""

    count: Any
    entity: Any
    simulation: Any

    @abc.abstractmethod
    def get_holder(self, variable_name: Any) -> Any:
        """Abstract method."""


class Role(Protocol):
    """Role protocol."""

    entity: Any
    subroles: Any


class Simulation(Protocol):
    """Simulation protocol."""

    trace: Any
    tracer: Any
    memory_config: Any
    data_storage_dir: Any
    tax_benefit_system: Any

    @abc.abstractmethod
    def calculate(self, variable_name: Any, period: Any) -> Any:
        """Abstract method."""

    @abc.abstractmethod
    def calculate_add(self, variable_name: Any, period: Any) -> Any:
        """Abstract method."""

    @abc.abstractmethod
    def calculate_divide(self, variable_name: Any, period: Any) -> Any:
        """Abstract method."""

    @abc.abstractmethod
    def get_population(self, plural: Optional[Any]) -> Any:
        """Abstract method."""


class TaxBenefitSystem(Protocol):
    """TaxBenefitSystem protocol."""

    person_entity: Any

    @abc.abstractmethod
    def get_variable(
            self, variable_name: Any,
            check_existence: Any = ...,
            ) -> Optional[Any]:
        """Abstract method."""


@typing_extensions.runtime_checkable
class Variable(Protocol):
    """Variable protocol."""

    name: Any
    dtype: Any
    entity: Any
    set_input: Any
    value_type: Any
    is_neutralized: Any
    definition_period: Any
