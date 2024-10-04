from __future__ import annotations

from collections.abc import Iterable, Sequence, Sized
from numpy.typing import NDArray
from typing import Any, NewType, TypeVar, Union
from typing_extensions import Protocol, TypeAlias

import numpy
import pendulum

_N_co = TypeVar("_N_co", bound=numpy.generic, covariant=True)

#: Type representing an numpy array.
Array: TypeAlias = NDArray[_N_co]

_L = TypeVar("_L")

#: Type representing an array-like object.
ArrayLike: TypeAlias = Sequence[_L]

#: Generic type vars.
_T_co = TypeVar("_T_co", covariant=True)


# Entities

#: For example "person".
EntityKey = NewType("EntityKey", str)

#: For example "persons".
EntityPlural = NewType("EntityPlural", str)

#: For example "principal".
RoleKey = NewType("RoleKey", str)

#: For example "parents".
RolePlural = NewType("RolePlural", str)


class CoreEntity(Protocol):
    key: EntityKey
    plural: EntityPlural

    def check_role_validity(self, role: object, /) -> None: ...
    def check_variable_defined_for_entity(
        self,
        variable_name: VariableName,
        /,
    ) -> None: ...
    def get_variable(
        self,
        variable_name: VariableName,
        check_existence: bool = ...,
        /,
    ) -> None | Variable: ...


class SingleEntity(CoreEntity, Protocol): ...


class GroupEntity(CoreEntity, Protocol): ...


class Role(Protocol):
    entity: GroupEntity
    max: int | None
    subroles: None | Iterable[Role]

    @property
    def key(self, /) -> RoleKey: ...
    @property
    def plural(self, /) -> None | RolePlural: ...


# Holders


class Holder(Protocol):
    def clone(self, population: Any, /) -> Holder: ...
    def get_memory_usage(self, /) -> Any: ...


# Parameters


class ParameterNodeAtInstant(Protocol): ...


# Periods

#: For example "2000-01".
InstantStr = NewType("InstantStr", str)

#: For example "1:2000-01-01:day".
PeriodStr = NewType("PeriodStr", str)


class Container(Protocol[_T_co]):
    def __contains__(self, item: object, /) -> bool: ...


class Indexable(Protocol[_T_co]):
    def __getitem__(self, index: int, /) -> _T_co: ...


class DateUnit(Container[str], Protocol):
    def upper(self, /) -> str: ...


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
    def unit(self, /) -> DateUnit: ...
    @property
    def start(self, /) -> Instant: ...
    @property
    def size(self, /) -> int: ...
    @property
    def stop(self, /) -> Instant: ...
    def offset(self, offset: str | int, unit: None | DateUnit = None, /) -> Period: ...


# Populations


class Population(Protocol):
    entity: Any

    def get_holder(self, variable_name: VariableName, /) -> Any: ...


# Simulations


class Simulation(Protocol):
    def calculate(self, variable_name: VariableName, period: Any, /) -> Any: ...
    def calculate_add(self, variable_name: VariableName, period: Any, /) -> Any: ...
    def calculate_divide(self, variable_name: VariableName, period: Any, /) -> Any: ...
    def get_population(self, plural: None | str, /) -> Any: ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    person_entity: Any

    def get_variable(
        self,
        variable_name: VariableName,
        check_existence: bool = ...,
        /,
    ) -> None | Variable: ...


# Variables

#: For example "salary".
VariableName = NewType("VariableName", str)


class Variable(Protocol):
    entity: Any
    name: VariableName


class Formula(Protocol):
    def __call__(
        self,
        population: Population,
        instant: Instant,
        params: Params,
        /,
    ) -> Array[Any]: ...


class Params(Protocol):
    def __call__(self, instant: Instant, /) -> ParameterNodeAtInstant: ...
