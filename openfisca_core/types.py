from __future__ import annotations

import typing_extensions
from collections.abc import Sequence
from numpy.typing import NDArray
from typing import Any, TypeVar
from typing_extensions import Protocol, TypeAlias

import abc

import numpy

N = TypeVar("N", bound=numpy.generic, covariant=True)

#: Type representing an numpy array.
Array: TypeAlias = NDArray[N]

L = TypeVar("L")

#: Type representing an array-like object.
ArrayLike: TypeAlias = Sequence[L]

#: Type variable representing an error.
E = TypeVar("E", covariant=True)

#: Type variable representing a value.
A = TypeVar("A", covariant=True)


# Entities


class Entity(Protocol):
    key: Any
    plural: Any

    @abc.abstractmethod
    def check_role_validity(self, role: Any) -> None:
        ...

    @abc.abstractmethod
    def check_variable_defined_for_entity(self, variable_name: Any) -> None:
        ...

    @abc.abstractmethod
    def get_variable(
        self,
        variable_name: Any,
        check_existence: Any = ...,
    ) -> Any | None:
        ...


class Role(Protocol):
    entity: Any
    subroles: Any


# Holders


class Holder(Protocol):
    @abc.abstractmethod
    def clone(self, population: Any) -> Holder:
        ...

    @abc.abstractmethod
    def get_memory_usage(self) -> Any:
        ...


# Parameters


@typing_extensions.runtime_checkable
class ParameterNodeAtInstant(Protocol):
    ...


# Periods


class Instant(Protocol):
    ...


@typing_extensions.runtime_checkable
class Period(Protocol):
    @property
    @abc.abstractmethod
    def start(self) -> Any:
        ...

    @property
    @abc.abstractmethod
    def unit(self) -> Any:
        ...


# Populations


class Population(Protocol):
    entity: Any

    @abc.abstractmethod
    def get_holder(self, variable_name: Any) -> Any:
        ...


# Simulations


class Simulation(Protocol):
    @abc.abstractmethod
    def calculate(self, variable_name: Any, period: Any) -> Any:
        ...

    @abc.abstractmethod
    def calculate_add(self, variable_name: Any, period: Any) -> Any:
        ...

    @abc.abstractmethod
    def calculate_divide(self, variable_name: Any, period: Any) -> Any:
        ...

    @abc.abstractmethod
    def get_population(self, plural: Any | None) -> Any:
        ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    person_entity: Any

    @abc.abstractmethod
    def get_variable(
        self,
        variable_name: Any,
        check_existence: Any = ...,
    ) -> Any | None:
        """Abstract method."""


# Variables


class Variable(Protocol):
    entity: Any


class Formula(Protocol):
    @abc.abstractmethod
    def __call__(
        self,
        population: Population,
        instant: Instant,
        params: Params,
    ) -> Array[Any]:
        ...


class Params(Protocol):
    @abc.abstractmethod
    def __call__(self, instant: Instant) -> ParameterNodeAtInstant:
        ...
