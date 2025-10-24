from __future__ import annotations

from collections.abc import Iterator

import sys
import time

from openfisca_core import types as t

from .computation_log import ComputationLog
from .flat_trace import FlatTrace
from .performance_log import PerformanceLog
from .simple_tracer import SimpleTracer
from .trace_node import TraceNode


class FullTracer:
    _simple_tracer: t.SimpleTracer
    _trees: list[t.TraceNode]
    _current_node: None | t.TraceNode

    def __init__(self) -> None:
        self._simple_tracer = SimpleTracer()
        self._trees = []
        self._current_node = None

    @property
    def stack(self) -> t.SimpleStack:
        """Return the stack of traces."""
        return self._simple_tracer.stack

    @property
    def trees(self) -> list[t.TraceNode]:
        """Return the tree of traces."""
        return self._trees

    @property
    def computation_log(self) -> t.ComputationLog:
        """Return the computation log."""
        return ComputationLog(self)

    @property
    def performance_log(self) -> t.PerformanceLog:
        """Return the performance log."""
        return PerformanceLog(self)

    @property
    def flat_trace(self) -> t.FlatTrace:
        """Return the flat trace."""
        return FlatTrace(self)

    def record_calculation_start(
        self,
        variable: t.VariableName,
        period: t.PeriodInt | t.Period,
    ) -> None:
        self._simple_tracer.record_calculation_start(variable, period)
        self._enter_calculation(variable, period)
        self._record_start_time()

    def record_parameter_access(
        self,
        parameter: str,
        period: t.Period,
        value: t.VarArray,
    ) -> None:
        if self._current_node is not None:
            self._current_node.parameters.append(
                TraceNode(name=parameter, period=period, value=value),
            )

    def record_calculation_result(self, value: t.VarArray) -> None:
        if self._current_node is not None:
            self._current_node.value = value

    def record_calculation_end(self) -> None:
        self._simple_tracer.record_calculation_end()
        self._record_end_time()
        self._exit_calculation()

    def print_computation_log(
        self, aggregate: bool = False, max_depth: int = sys.maxsize
    ) -> None:
        self.computation_log.print_log(aggregate, max_depth)

    def generate_performance_graph(self, dir_path: str) -> None:
        self.performance_log.generate_graph(dir_path)

    def generate_performance_tables(self, dir_path: str) -> None:
        self.performance_log.generate_performance_tables(dir_path)

    def get_nb_requests(self, variable: str) -> int:
        return sum(self._get_nb_requests(tree, variable) for tree in self.trees)

    def get_flat_trace(self) -> t.FlatNodeMap:
        return self.flat_trace.get_trace()

    def get_serialized_flat_trace(self) -> t.SerializedNodeMap:
        return self.flat_trace.get_serialized_trace()

    def browse_trace(self) -> Iterator[t.TraceNode]:
        def _browse_node(node: t.TraceNode) -> Iterator[t.TraceNode]:
            yield node

            for child in node.children:
                yield from _browse_node(child)

        for node in self._trees:
            yield from _browse_node(node)

    def _enter_calculation(
        self,
        variable: t.VariableName,
        period: t.PeriodInt | t.Period,
    ) -> None:
        new_node = TraceNode(
            name=variable,
            period=period,
            parent=self._current_node,
        )

        if self._current_node is None:
            self._trees.append(new_node)

        else:
            self._current_node.append_child(new_node)

        self._current_node = new_node

    def _record_start_time(
        self,
        time_in_s: float | None = None,
    ) -> None:
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        if self._current_node is not None:
            self._current_node.start = time_in_s

    def _record_end_time(
        self,
        time_in_s: None | t.Time = None,
    ) -> None:
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        if self._current_node is not None:
            self._current_node.end = time_in_s

    def _exit_calculation(self) -> None:
        if self._current_node is not None:
            self._current_node = self._current_node.parent

    def _get_nb_requests(self, tree: t.TraceNode, variable: str) -> int:
        tree_call = tree.name == variable
        children_calls = sum(
            self._get_nb_requests(child, variable) for child in tree.children
        )

        return tree_call + children_calls

    @staticmethod
    def _get_time_in_sec() -> t.Time:
        return time.time_ns() / (10**9)


__all__ = ["FullTracer"]
