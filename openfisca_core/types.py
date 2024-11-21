from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    KeysView,
    MutableMapping,
    Sequence,
    Sized,
)
from numpy.typing import DTypeLike, NDArray
from typing import NewType, TypeVar, Union
from typing_extensions import Protocol, Required, Self, TypeAlias, TypedDict

import abc
import datetime
import enum
import re
from enum import _EnumDict as EnumDict  # noqa: PLC2701

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

#: Type var for numpy arrays (invariant).
_N = TypeVar("_N", bound=VarDType)

#: Type var for numpy arrays (covariant).
_N_co = TypeVar("_N_co", covariant=True, bound=VarDType)

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


# Data storage


class CoreStorage(Protocol[_N]):
    def get(self, __period: None | Period, /) -> None | Array[_N]: ...
    def put(self, __value: Array[_N], __period: None | Period, /) -> None: ...
    def delete(self, __period: None | Period = ..., /) -> None: ...
    def get_known_periods(self, /) -> KeysView[Period]: ...


class InMemoryStorage(CoreStorage[_N], Protocol):
    def get_memory_usage(self, /) -> MemoryUsage: ...


class OnDiskStorage(CoreStorage[_N], Protocol):
    def restore(self, /) -> None: ...


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
    @property
    def key(self, /) -> EntityKey: ...
    @property
    def plural(self, /) -> EntityPlural: ...
    @property
    def label(self, /) -> str: ...
    @property
    def doc(self, /) -> str: ...
    def set_tax_benefit_system(self, __tbs: TaxBenefitSystem, /) -> None: ...
    def get_variable(
        self, __name: VariableName, __check: bool = ..., /
    ) -> None | Variable[VarDType]: ...
    def check_variable_defined_for_entity(
        self,
        __name: VariableName,
        /,
    ) -> None: ...
    @staticmethod
    def check_role_validity(__role: object, /) -> None: ...


class SingleEntity(CoreEntity, Protocol): ...


class GroupEntity(CoreEntity, Protocol):
    @property
    def roles(self, /) -> Iterable[Role]: ...
    @property
    def flattened_roles(self, /) -> Iterable[Role]: ...


class Role(Protocol):
    @property
    def entity(self, /) -> GroupEntity: ...
    @property
    def max(self, /) -> None | int: ...
    @property
    def subroles(self, /) -> None | Iterable[Role]: ...
    @property
    def key(self, /) -> RoleKey: ...
    @property
    def plural(self, /) -> None | RolePlural: ...
    @property
    def label(self, /) -> None | str: ...
    @property
    def doc(self, /) -> None | str: ...


class RoleParams(TypedDict, total=False):
    key: Required[str]
    plural: str
    label: str
    doc: str
    max: int
    subroles: list[str]


# Experimental


class MemoryConfig(Protocol):
    @property
    def max_memory_occupation(self, /) -> float: ...
    @property
    def max_memory_occupation_pc(self, /) -> float: ...
    @property
    def priority_variables(self, /) -> frozenset[str]: ...
    @property
    def variables_to_drop(self, /) -> frozenset[str]: ...


# Indexed enums


class EnumType(enum.EnumMeta):
    indices: IndexArray
    names: StrArray
    enums: ObjArray


class Enum(enum.Enum, metaclass=EnumType):
    index: int
    _member_names_: list[str]

    @classmethod
    @abc.abstractmethod
    def encode(
        cls, __array: Array[_N] | ArrayLike[object], /
    ) -> EnumArray[EnumDType]: ...


class EnumArray(Array[_N]):
    possible_values: None | type[Enum]

    @abc.abstractmethod
    def __new__(cls, /, __array: Array[_N], __enum: type[Enum]) -> Self: ...
    @abc.abstractmethod
    def decode(self, /) -> ObjArray: ...
    @abc.abstractmethod
    def decode_to_str(self, /) -> StrArray: ...


# Holders


class Holder(Protocol[_N]):
    @property
    def population(self, /) -> CorePopulation: ...
    @property
    def simulation(self, /) -> None | Simulation: ...
    @property
    def variable(self, /) -> Variable[_N]: ...
    @property
    def _eternal(self, /) -> bool: ...
    @property
    def _memory_storage(self, /) -> InMemoryStorage[_N]: ...
    @property
    def _disk_storage(self, /) -> None | OnDiskStorage[_N]: ...
    @property
    def _on_disk_storable(self, /) -> bool: ...
    @property
    def _do_not_store(self, /) -> bool: ...
    def clone(self, __population: CorePopulation, /) -> Holder[_N]: ...
    def create_disk_storage(
        self, __dir: None | str = ..., __preserve: bool = ..., /
    ) -> OnDiskStorage[_N]: ...
    def delete_arrays(self, __period: None | Period = None, /) -> None: ...
    def get_array(self, __period: Period, /) -> None | Array[_N]: ...
    def get_memory_usage(self, /) -> MemoryUsage: ...
    def get_known_periods(self) -> list[Period]: ...
    def set_input(
        self,
        __period: Period,
        __array: Array[_N] | ArrayLike[_L],
        /,
    ) -> None | Array[_N]: ...
    def put_in_cache(self, __value: Array[_N], period: Period, /) -> None: ...
    def default_array(self, /) -> Array[_N]: ...
    def _set(self, __period: None | Period, __value: Array[_N], /) -> None: ...
    def _to_array(self, __value: Array[_N] | ArrayLike[_L], /) -> Array[_N]: ...


class MemoryUsage(TypedDict, total=False):
    cell_size: float
    dtype: DTypeLike
    nb_arrays: Required[int]
    nb_cells_by_array: int
    nb_requests: int
    nb_requests_by_array: float
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
    def __getitem__(self, __index: str | VarArray, /) -> ParameterNodeChild: ...


class VectorialParameterNodeAtInstant(Protocol):
    _instant_str: InstantStr

    def __contains__(self, __item: object, /) -> bool: ...
    def __getitem__(self, __index: str | VarArray, /) -> ParameterNodeChild: ...


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

#: Type alias for a population's holders.
HolderByVariable: TypeAlias = MutableMapping["VariableName", Holder[_N]]


class MemoryUsageByVariable(TypedDict, total=False):
    by_variable: dict[VariableName, MemoryUsage]
    total_nb_bytes: int


class CorePopulation(Protocol):
    @property
    def count(self, /) -> int: ...
    @property
    def entity(self, /) -> CoreEntity: ...
    @property
    def ids(self, /) -> ArrayLike[str]: ...
    @property
    def simulation(self, /) -> None | Simulation: ...
    @property
    def _holders(self, /) -> HolderByVariable[_N]: ...


class SinglePopulation(CorePopulation, Protocol):
    @property
    def entity(self, /) -> SingleEntity: ...
    def get_holder(self, __name: VariableName, /) -> Holder[VarDType]: ...


class GroupPopulation(CorePopulation, Protocol):
    @property
    def entity(self, /) -> GroupEntity: ...
    @property
    def members_entity_id(self, /) -> StrArray: ...
    def nb_persons(self, /, __role: None | Role = ...) -> int: ...


# TODO(Mauko Quiroga-Alvarado): I'm not sure if this type alias is correct.
# https://openfisca.org/doc/coding-the-legislation/50_entities.html
Members: TypeAlias = Iterable[SinglePopulation]


# Simulations


class Simulation(Protocol):
    @property
    def data_storage_dir(self, /) -> str: ...
    @property
    def opt_out_cache(self, /) -> bool: ...
    @property
    def memory_config(self, /) -> None | MemoryConfig: ...
    @property
    def populations(self, /) -> MutableMapping[str, CorePopulation]: ...
    @property
    def tax_benefit_system(self, /) -> TaxBenefitSystem: ...
    @property
    def trace(self, /) -> bool: ...
    @property
    def tracer(self, /) -> FullTracer: ...
    def calculate(self, __name: VariableName, __period: Period, /) -> VarArray: ...
    def calculate_add(self, __name: VariableName, __period: Period, /) -> VarArray: ...
    def calculate_divide(
        self, __name: VariableName, __period: Period, /
    ) -> VarArray: ...
    def get_population(self, __plural: None | str, /) -> CorePopulation: ...


# Tax-Benefit systems


class TaxBenefitSystem(Protocol):
    @property
    def cache_blacklist(self, /) -> frozenset[VariableName]: ...
    @property
    def person_entity(self, /) -> SingleEntity: ...
    @person_entity.setter
    def person_entity(self, /, __entity: SingleEntity) -> None: ...
    def variables(self, /) -> dict[VariableName, Variable[VarDType]]: ...
    def entities_by_singular(self, /) -> dict[EntityKey, CoreEntity]: ...
    def entities_plural(self, /) -> Iterable[EntityPlural]: ...
    def get_variable(
        self,
        __name: VariableName,
        __check: bool = ...,
        /,
    ) -> None | Variable[VarDType]: ...
    def instantiate_entities(self, /) -> dict[str, CorePopulation]: ...


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


class Variable(Protocol[_N]):
    @property
    def definition_period(self, /) -> DateUnit: ...
    @property
    def dtype(self, /) -> DTypeLike: ...
    @property
    def end(self, /) -> PeriodStr: ...
    @property
    def entity(self, /) -> CoreEntity: ...
    @property
    def holder(self, /) -> Holder[_N]: ...
    @property
    def is_neutralized(self, /) -> bool: ...
    @property
    def name(self, /) -> VariableName: ...
    @property
    def value_type(
        self, /
    ) -> type[bool | int | float | str | Enum | datetime.date]: ...
    def default_array(self, /, __size: int) -> Array[_N]: ...


class Formula(Protocol):
    def __call__(
        self,
        __population: CorePopulation,
        __instant: Instant,
        __params: Params,
        /,
    ) -> VarArray: ...


class Params(Protocol):
    def __call__(self, __instant: Instant, /) -> ParameterNodeAtInstant: ...


__all__ = ["DTypeLike", "EnumDict"]
