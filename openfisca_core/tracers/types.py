from __future__ import annotations

from collections.abc import Iterator
from typing import NewType, Protocol
from typing_extensions import TypeAlias, TypedDict

from openfisca_core.types import (
    Array,
    ArrayLike,
    ParameterNode,
    ParameterNodeChild,
    Period,
    PeriodInt,
    VariableName,
)

from numpy import generic as VarDType

#: A type of a generic array.
VarArray: TypeAlias = Array[VarDType]

#: A type representing a unit time.
Time: TypeAlias = float

#: A type representing a mapping of flat traces.
FlatNodeMap: TypeAlias = dict["NodeKey", "FlatTraceMap"]

#: A type representing a mapping of serialized traces.
SerializedNodeMap: TypeAlias = dict["NodeKey", "SerializedTraceMap"]

#: A stack of simple traces.
SimpleStack: TypeAlias = list["SimpleTraceMap"]

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
    def print_log(self, aggregate: bool = ..., max_depth: int = ..., /) -> None: ...


class FlatTrace(Protocol):
    def get_trace(self, /) -> FlatNodeMap: ...
    def get_serialized_trace(self, /) -> SerializedNodeMap: ...


class FullTracer(Protocol):
    @property
    def trees(self, /) -> list[TraceNode]: ...
    def browse_trace(self, /) -> Iterator[TraceNode]: ...


class PerformanceLog(Protocol):
    def generate_graph(self, dir_path: str, /) -> None: ...
    def generate_performance_tables(self, dir_path: str, /) -> None: ...


class SimpleTracer(Protocol):
    @property
    def stack(self, /) -> SimpleStack: ...
    def record_calculation_start(
        self, variable: VariableName, period: PeriodInt | Period, /
    ) -> None: ...
    def record_calculation_end(self, /) -> None: ...


class TraceNode(Protocol):
    children: list[TraceNode]
    end: Time
    name: str
    parameters: list[TraceNode]
    parent: None | TraceNode
    period: PeriodInt | Period
    start: Time
    value: None | VarArray

    def calculation_time(self, *, round_: bool = ...) -> Time: ...
    def formula_time(self, /) -> Time: ...
    def append_child(self, node: TraceNode, /) -> None: ...


__all__ = [
    "ArrayLike",
    "ParameterNode",
    "ParameterNodeChild",
    "PeriodInt",
]
