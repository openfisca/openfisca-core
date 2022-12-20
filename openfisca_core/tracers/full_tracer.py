from __future__ import annotations

import time
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

from openfisca_core import types

from .computation_log import ComputationLog
from .flat_trace import FlatTrace
from .performance_log import PerformanceLog
from .simple_tracer import SimpleTracer
from .trace_node import TraceNode

Stack = List[Dict[str, Union[str, types.Period]]]
Value = Union[types.Array[Any], Sequence[Any]]


class FullTracer:
    _simple_tracer: SimpleTracer
    _trees: list
    _current_node: Optional[types.TraceNode]

    def __init__(self) -> None:
        self._simple_tracer = SimpleTracer()
        self._trees = []
        self._current_node = None

    def record_calculation_start(
            self,
            variable: str,
            period: types.Period,
            ) -> None:
        self._simple_tracer.record_calculation_start(variable, period)
        self._enter_calculation(variable, period)
        self._record_start_time()

    def _enter_calculation(
            self,
            variable: str,
            period: types.Period,
            ) -> None:
        new_node = TraceNode(
            name = variable,
            period = period,
            parent = self._current_node,
            )

        if self._current_node is None:
            self._trees.append(new_node)

        else:
            self._current_node.append_child(new_node)

        self._current_node = new_node

    def record_parameter_access(
            self,
            parameter: str,
            period: types.Period,
            value: Value,
            ) -> None:

        if self._current_node is not None:
            self._current_node.parameters = (
                *self._current_node.parameters,
                TraceNode(parameter, period, value = value),
                )

    def _record_start_time(
            self,
            time_in_s: Optional[float] = None,
            ) -> None:
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        if self._current_node is not None:
            self._current_node.start = time_in_s

    def record_calculation_result(self, value: Value) -> None:
        if self._current_node is not None:
            self._current_node.value = value

    def record_calculation_end(self) -> None:
        self._simple_tracer.record_calculation_end()
        self._record_end_time()
        self._exit_calculation()

    def _record_end_time(
            self,
            time_in_s: Optional[float] = None,
            ) -> None:
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        if self._current_node is not None:
            self._current_node.end = time_in_s

    def _exit_calculation(self) -> None:
        if self._current_node is not None:
            self._current_node = self._current_node.parent

    @property
    def stack(self) -> Stack:
        return self._simple_tracer.stack

    @property
    def trees(self) -> List[TraceNode]:
        return self._trees

    @property
    def computation_log(self) -> ComputationLog:
        return ComputationLog(self)

    @property
    def performance_log(self) -> PerformanceLog:
        return PerformanceLog(self)

    @property
    def flat_trace(self) -> FlatTrace:
        return FlatTrace(self)

    def _get_time_in_sec(self) -> float:
        return time.time_ns() / (10**9)

    def print_computation_log(self, aggregate = False, max_depth = None):
        self.computation_log.print_log(aggregate, max_depth)

    def generate_performance_graph(self, dir_path: str) -> None:
        self.performance_log.generate_graph(dir_path)

    def generate_performance_tables(self, dir_path: str) -> None:
        self.performance_log.generate_performance_tables(dir_path)

    def _get_nb_requests(self, tree: TraceNode, variable: str) -> int:
        tree_call = tree.name == variable
        children_calls = sum(
            self._get_nb_requests(child, variable)
            for child
            in tree.children
            )

        return tree_call + children_calls

    def get_nb_requests(self, variable: str) -> int:
        return sum(
            self._get_nb_requests(tree, variable)
            for tree
            in self.trees
            )

    def get_flat_trace(self) -> dict:
        return self.flat_trace.get_trace()

    def get_serialized_flat_trace(self) -> dict:
        return self.flat_trace.get_serialized_trace()

    def browse_trace(self) -> Iterator[TraceNode]:

        def _browse_node(node):
            yield node

            for child in node.children:
                yield from _browse_node(child)

        for node in self._trees:
            yield from _browse_node(node)
