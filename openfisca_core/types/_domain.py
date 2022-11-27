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
            instant: Instant,
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


class Instant(Protocol):
    """Instant protocol."""


class Params(Protocol):
    """Params protocol."""

    @abc.abstractmethod
    def __call__(self, instant: Instant) -> ParameterNodeAtInstant:
        """Abstract method."""


@typing_extensions.runtime_checkable
class Period(Protocol):
    """Period protocol."""

    @property
    @abc.abstractmethod
    def start(self) -> Any:
        """Abstract method."""


class Population(Protocol):
    """Population protocol."""

    entity: Any

    @abc.abstractmethod
    def get_holder(self, variable_name: Any) -> Any:
        """Abstract method."""


class Role(Protocol):
    """Role protocol."""

    entity: Any
    subroles: Any


class Simulation(Protocol):
    """Simulation protocol."""

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


class Variable(Protocol):
    """Variable protocol."""

    entity: Any
