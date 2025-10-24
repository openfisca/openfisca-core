from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence, Sized
from numpy.typing import DTypeLike, NDArray
from typing import NewType, TypeVar, Union
from typing_extensions import Protocol, Required, Self, TypeAlias, TypedDict

import abc
import enum
import re

import numpy
import pendulum
from numpy import (
    bool_ as BoolDType,
    bytes_ as BytesDType,
    datetime64 as DateDType,
    float32 as FloatDType,
    generic as VarDType,
    int32 as IntDType,
    object_ as ObjDType,
    str_ as StrDType,
    uint8 as EnumDType,
)

#: Generic covariant type var.
_T_co = TypeVar("_T_co", covariant=True)

# Arrays

#: Type var for numpy arrays.
_N_co = TypeVar("_N_co", covariant=True, bound="DTypeGeneric")

#: Type representing an numpy array.
Array: TypeAlias = NDArray[_N_co]

#: Type alias for a boolean array.
BoolArray: TypeAlias = Array[BoolDType]

#: Type alias for an array of bytes.
BytesArray: TypeAlias = Array[BytesDType]

#: Type alias for an array of dates.
DateArray: TypeAlias = Array[DateDType]

#: Type alias for an array of floats.
FloatArray: TypeAlias = Array[FloatDType]

#: Type alias for an array of enum indices.
IndexArray: TypeAlias = Array[EnumDType]

#: Type alias for an array of integers.
IntArray: TypeAlias = Array[IntDType]

#: Type alias for an array of objects.
ObjArray: TypeAlias = Array[ObjDType]

#: Type alias for an array of strings.
StrArray: TypeAlias = Array[StrDType]

#: Type alias for an array of generic objects.
VarArray: TypeAlias = Array[VarDType]

# Arrays-like

#: Type var for array-like objects.
_L = TypeVar("_L")

#: Type representing an array-like object.
ArrayLike: TypeAlias = Sequence[_L]

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

# TODO(<Mauko Quiroga-Alvarado>): Properly resolve metaclass types.
# https://github.com/python/mypy/issues/14033


class _SeqIntMeta(type):
    def __instancecheck__(self, arg: object, /) -> bool:
        return (
            bool(arg)
            and isinstance(arg, Sequence)
            and all(isinstance(item, int) for item in arg)
        )


class SeqInt(list[int], metaclass=_SeqIntMeta): ...  # type: ignore[misc]


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
    indices: Array[DTypeEnum]
    names: Array[DTypeStr]
    enums: Array[DTypeObject]


class Enum(enum.Enum, metaclass=EnumType):
    index: int
    _member_names_: list[str]


class EnumArray(Array[DTypeEnum], metaclass=abc.ABCMeta):
    possible_values: None | type[Enum]

    @abc.abstractmethod
    def __new__(
        cls, input_array: Array[DTypeEnum], possible_values: type[Enum]
    ) -> Self: ...


# Holders


class Holder(Protocol):
    def clone(self, population: CorePopulation, /) -> Holder: ...

    def get_memory_usage(self, /) -> MemoryUsage: ...


class MemoryUsage(TypedDict, total=False):
    cell_size: int
    dtype: DTypeLike
    nb_arrays: int
    nb_cells_by_array: int
    nb_requests: int
    nb_requests_by_array: int
    total_nb_bytes: Required[int]


# Parameters

#: A type representing a node of parameters.
ParameterNode: TypeAlias = Union[
    "ParameterNodeAtInstant", "VectorialParameterNodeAtInstant"
]

#: A type representing a ???
ParameterNodeChild: TypeAlias = Union[ParameterNode, ArrayLike[object]]


class ParameterNodeAtInstant(Protocol):
    _instant_str: InstantStr

    def __contains__(self, __item: object, /) -> bool: ...

    def __getitem__(
        self, __index: str | Array[DTypeGeneric], /
    ) -> ParameterNodeChild: ...


class VectorialParameterNodeAtInstant(Protocol):
    _instant_str: InstantStr

    def __contains__(self, item: object, /) -> bool: ...

    def __getitem__(
        self, __index: str | Array[DTypeGeneric], /
    ) -> ParameterNodeChild: ...


# Periods

#: Matches "2015", "2015-01", "2015-01-01" but not "2015-13", "2015-12-32".
iso_format = re.compile(r"^\d{4}(-(?:0[1-9]|1[0-2])(-(?:0[1-9]|[12]\d|3[01]))?)?$")

#: Matches "2015", "2015-W01", "2015-W53-1" but not "2015-W54", "2015-W10-8".
iso_calendar = re.compile(r"^\d{4}(-W(0[1-9]|[1-4][0-9]|5[0-3]))?(-[1-7])?$")

#: For example 2020.
InstantInt = NewType("InstantInt", int)

#: For example 2020.
PeriodInt = NewType("PeriodInt", int)


class _InstantStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, (ISOFormatStr, ISOCalendarStr))


class InstantStr(str, metaclass=_InstantStrMeta):  # type: ignore[misc]
    __slots__ = ()


class _ISOFormatStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, str) and bool(iso_format.match(arg))


class ISOFormatStr(str, metaclass=_ISOFormatStrMeta):  # type: ignore[misc]
    __slots__ = ()


class _ISOCalendarStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, str) and bool(iso_calendar.match(arg))


class ISOCalendarStr(str, metaclass=_ISOCalendarStrMeta):  # type: ignore[misc]
    __slots__ = ()


class _PeriodStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return (
            isinstance(arg, str)
            and ":" in arg
            and isinstance(arg.split(":")[1], InstantStr)
        )


class PeriodStr(str, metaclass=_PeriodStrMeta):  # type: ignore[misc]
    __slots__ = ()


class Container(Protocol[_T_co]):
    def __contains__(self, __item: object, /) -> bool: ...


class Indexable(Protocol[_T_co]):
    def __getitem__(self, __index: int, /) -> _T_co: ...


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

    def __lt__(self, __other: object, /) -> bool: ...

    def __le__(self, __other: object, /) -> bool: ...

    def offset(self, __offset: str | int, __unit: DateUnit, /) -> None | Instant: ...


class Period(Indexable[Union[DateUnit, Instant, int]], Protocol):
    @property
    def unit(self, /) -> DateUnit: ...

    @property
    def start(self, /) -> Instant: ...

    @property
    def size(self, /) -> int: ...

    @property
    def stop(self, /) -> Instant: ...

    def contains(self, __other: Period, /) -> bool: ...

    def offset(
        self, __offset: str | int, __unit: None | DateUnit = None, /
    ) -> Period: ...


#: Type alias for a period-like object.
PeriodLike: TypeAlias = Union[Period, PeriodStr, PeriodInt]

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


# Tracers

#: A type representing a unit time.
Time: TypeAlias = float

#: A type representing a mapping of flat traces.
FlatNodeMap: TypeAlias = dict["NodeKey", "FlatTraceMap"]

#: A type representing a mapping of serialized traces.
SerializedNodeMap: TypeAlias = dict["NodeKey", "SerializedTraceMap"]

#: Key of a trace.
NodeKey = NewType("NodeKey", str)


class FlatTraceMap(TypedDict, total=True):
    dependencies: list[NodeKey]
    parameters: dict[NodeKey, None | ArrayLike[object]]
    value: None | VarArray
    calculation_time: Time
    formula_time: Time


class SerializedTraceMap(TypedDict, total=True):
    dependencies: list[NodeKey]
    parameters: dict[NodeKey, None | ArrayLike[object]]
    value: None | ArrayLike[object]
    calculation_time: Time
    formula_time: Time


class SimpleTraceMap(TypedDict, total=True):
    name: VariableName
    period: int | Period


class ComputationLog(Protocol):
    def print_log(self, __aggregate: bool = ..., __max_depth: int = ..., /) -> None: ...


class FlatTrace(Protocol):
    def get_trace(self, /) -> FlatNodeMap: ...

    def get_serialized_trace(self, /) -> SerializedNodeMap: ...


class FullTracer(Protocol):
    @property
    def trees(self, /) -> list[TraceNode]: ...

    def browse_trace(self, /) -> Iterator[TraceNode]: ...

    def get_nb_requests(self, __name: VariableName, /) -> int: ...


class PerformanceLog(Protocol):
    def generate_graph(self, __dir_path: str, /) -> None: ...

    def generate_performance_tables(self, __dir_path: str, /) -> None: ...


class SimpleTracer(Protocol):
    @property
    def stack(self, /) -> SimpleStack: ...

    def record_calculation_start(
        self, __name: VariableName, __period: PeriodInt | Period, /
    ) -> None: ...

    def record_calculation_end(self, /) -> None: ...


class TraceNode(Protocol):
    @property
    def children(self, /) -> list[TraceNode]: ...

    @property
    def end(self, /) -> Time: ...

    @property
    def name(self, /) -> str: ...

    @property
    def parameters(self, /) -> list[TraceNode]: ...

    @property
    def parent(self, /) -> None | TraceNode: ...

    @property
    def period(self, /) -> PeriodInt | Period: ...

    @property
    def start(self, /) -> Time: ...

    @property
    def value(self, /) -> None | VarArray: ...

    def calculation_time(self, *, __round: bool = ...) -> Time: ...

    def formula_time(self, /) -> Time: ...

    def append_child(self, __node: TraceNode, /) -> None: ...


#: A stack of simple traces.
SimpleStack: TypeAlias = list[SimpleTraceMap]

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
