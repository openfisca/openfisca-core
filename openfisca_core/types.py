from __future__ import annotations

from collections.abc import Iterable, Sequence, Sized
from numpy.typing import NDArray
from typing import Any, TypeVar, Union
from typing_extensions import NewType, Protocol, TypeAlias

import numpy
import pendulum

_N = TypeVar("_N", bound=numpy.generic, covariant=True)

#: Type representing an numpy array.
Array: TypeAlias = NDArray[_N]

_L = TypeVar("_L")

#: Type representing an array-like object.
ArrayLike: TypeAlias = Sequence[_L]

#: Type variable representing an error.
_E = TypeVar("_E", covariant=True)

#: Type variable representing a value.
_A = TypeVar("_A", covariant=True)

#: Generic type vars.
_T_cov = TypeVar("_T_cov", covariant=True)
_T_con = TypeVar("_T_con", contravariant=True)


# Entities


class CoreEntity(Protocol):
    key: Any
    plural: Any

    def check_role_validity(self, role: Any) -> None: ...
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
    def clone(self, population: Any) -> Holder: ...
    def get_memory_usage(self) -> Any: ...


# Parameters


class ParameterNodeAtInstant(Protocol): ...


# Periods

#: For example "2000-01".
InstantStr = NewType("InstantStr", str)

#: For example "1:2000-01-01:day".
PeriodStr = NewType("PeriodStr", str)


class Indexable(Protocol[_T_cov]):
    def __getitem__(self, index: int, /) -> _T_cov: ...


class DateUnit(Protocol):
    def __contains__(self, other: object, /) -> bool: ...
    def upper(self) -> str: ...


class Instant(Indexable[int], Iterable[int], Sized, Protocol):
    @property
    def year(self, /) -> int: ...
    @property
    def month(self, /) -> int: ...
    @property
    def day(self, /) -> int: ...
    @property
    def date(self, /) -> pendulum.Date: ...
    def __lt__(self, other: object, /) -> bool: ...
    def __le__(self, other: object, /) -> bool: ...
    def offset(self, offset: str | int, unit: DateUnit, /) -> None | Instant: ...


class Period(Indexable[Union[DateUnit, Instant, int]], Protocol):
    @property
    def unit(self) -> DateUnit: ...
    @property
    def start(self) -> Instant: ...
    @property
    def size(self) -> int: ...
    @property
    def stop(self) -> Instant: ...
    def offset(self, offset: str | int, unit: None | DateUnit = None) -> Period: ...


# Populations


class Population(Protocol):
    entity: Any

    def get_holder(self, variable_name: Any) -> Any: ...


# Simulations


class Simulation(Protocol):
    def calculate(self, variable_name: Any, period: Any) -> Any: ...
    def calculate_add(self, variable_name: Any, period: Any) -> Any: ...
    def calculate_divide(self, variable_name: Any, period: Any) -> Any: ...
    def get_population(self, plural: Any | None) -> Any: ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    person_entity: Any

    def get_variable(
        self,
        variable_name: Any,
        check_existence: Any = ...,
    ) -> Any | None: ...


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
    def __call__(self, instant: Instant) -> ParameterNodeAtInstant: ...
