from __future__ import annotations

from collections.abc import Iterable, Sequence, Sized
from numpy.typing import DTypeLike, NDArray
from typing import Any, NewType, TypeVar, Union
from typing_extensions import Protocol, Self, TypeAlias

import abc
import enum

import numpy
import pendulum

#: Generic covariant type var.
_T_co = TypeVar("_T_co", covariant=True)

# Commons

#: Type var for numpy arrays.
_N_co = TypeVar("_N_co", covariant=True, bound="DTypeGeneric")

#: Type representing an numpy array.
Array: TypeAlias = NDArray[_N_co]

#: Type var for array-like objects.
_L = TypeVar("_L")

#: Type representing an array-like object.
ArrayLike: TypeAlias = Sequence[_L]

#: Type for record arrays.
RecArray: TypeAlias = numpy.recarray[object, Any]  # type: ignore[misc]

#: Type for bool arrays.
DTypeBool: TypeAlias = numpy.bool_

#: Type for int arrays.
DTypeInt: TypeAlias = numpy.int32

#: Type for float arrays.
DTypeFloat: TypeAlias = numpy.float32

#: Type for string arrays.
DTypeStr: TypeAlias = numpy.str_

#: Type for bytes arrays.
DTypeBytes: TypeAlias = numpy.bytes_

#: Type for Enum arrays.
DTypeEnum: TypeAlias = numpy.uint8

#: Type for date arrays.
DTypeDate: TypeAlias = numpy.datetime64

#: Type for "object" arrays.
DTypeObject: TypeAlias = numpy.object_

#: Type for "generic" arrays.
DTypeGeneric: TypeAlias = numpy.generic

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


# Indexed enums


class EnumType(enum.EnumMeta):
    items: RecArray

    @property
    @abc.abstractmethod
    def indices(cls) -> Array[DTypeEnum]: ...


class Enum(enum.Enum, metaclass=EnumType):
    index: int
    _member_names_: list[str]


class EnumArray(Array[DTypeEnum], metaclass=abc.ABCMeta):
    possible_values: None | type[Enum]

    @abc.abstractmethod
    def __new__(
        cls, input_array: Array[DTypeEnum], possible_values: None | type[Enum] = ...
    ) -> Self: ...


# Holders


class Holder(Protocol):
    def clone(self, population: CorePopulation, /) -> Holder: ...
    def get_memory_usage(self, /) -> dict[str, object]: ...


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
    def contains(self, other: Period, /) -> bool: ...
    def offset(self, offset: str | int, unit: None | DateUnit = None, /) -> Period: ...


# Populations


class CorePopulation(Protocol): ...


class SinglePopulation(CorePopulation, Protocol):
    entity: SingleEntity

    def get_holder(self, variable_name: VariableName, /) -> Holder: ...


class GroupPopulation(CorePopulation, Protocol): ...


# Simulations


class Simulation(Protocol):
    def calculate(
        self, variable_name: VariableName, period: Period, /
    ) -> Array[DTypeGeneric]: ...
    def calculate_add(
        self, variable_name: VariableName, period: Period, /
    ) -> Array[DTypeGeneric]: ...
    def calculate_divide(
        self, variable_name: VariableName, period: Period, /
    ) -> Array[DTypeGeneric]: ...
    def get_population(self, plural: None | str, /) -> CorePopulation: ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    person_entity: SingleEntity

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
    entity: CoreEntity
    name: VariableName


class Formula(Protocol):
    def __call__(
        self,
        population: CorePopulation,
        instant: Instant,
        params: Params,
        /,
    ) -> Array[DTypeGeneric]: ...


class Params(Protocol):
    def __call__(self, instant: Instant, /) -> ParameterNodeAtInstant: ...


__all__ = ["DTypeLike"]
