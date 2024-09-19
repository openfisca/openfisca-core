from __future__ import annotations

from collections.abc import Iterable, Sequence, Sized
from numpy.typing import NDArray
from typing import Any, TypeVar, Union
from typing_extensions import Protocol, TypeAlias

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

#: Generic type vars.
T_cov = TypeVar("T_cov", covariant=True)
T_con = TypeVar("T_con", contravariant=True)


# Entities


class CoreEntity(Protocol):
    key: Any
    plural: Any

    @abc.abstractmethod
    def check_role_validity(self, role: Any) -> None: ...

    @abc.abstractmethod
    def check_variable_defined_for_entity(self, variable_name: Any) -> None: ...

    def get_variable(
        self,
        variable_name: Any,
        check_existence: Any = ...,
    ) -> Any | None: ...


class SingleEntity(CoreEntity, Protocol): ...


class GroupEntity(CoreEntity, Protocol): ...


class Role(Protocol):
    entity: Any
    max: int | None
    subroles: Any

    @property
    def key(self) -> str: ...


# Holders


class Holder(Protocol):
    @abc.abstractmethod
    def clone(self, population: Any) -> Holder: ...

    @abc.abstractmethod
    def get_memory_usage(self) -> Any: ...


# Parameters


class ParameterNodeAtInstant(Protocol):
    ...


# Periods


class Indexable(Protocol[T_cov]):
    def __getitem__(self, index: int, /) -> T_cov:
        ...


class DateUnit(Protocol):
    def __contains__(self, other: object, /) -> bool:
        ...


class Instant(Indexable[int], Iterable[int], Sized, Protocol):
    ...


class Period(Indexable[Union[DateUnit, Instant, int]], Protocol):
    @property
    def unit(self) -> DateUnit:
        ...


# Populations


class Population(Protocol):
    entity: Any

    def get_holder(self, variable_name: Any) -> Any:
        ...


# Simulations


class Simulation(Protocol):
    def calculate(self, variable_name: Any, period: Any) -> Any:
        ...

    def calculate_add(self, variable_name: Any, period: Any) -> Any:
        ...

    def calculate_divide(self, variable_name: Any, period: Any) -> Any:
        ...

    def get_population(self, plural: Any | None) -> Any:
        ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    person_entity: Any

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
    def __call__(
        self,
        population: Population,
        instant: Instant,
        params: Params,
    ) -> Array[Any]: ...


class Params(Protocol):
    def __call__(self, instant: Instant) -> ParameterNodeAtInstant:
        ...
