from __future__ import annotations

import time
import typing
from typing import Dict, Iterator, List, Optional, Union

from .. import tracers

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from policyengine_core.periods import Period

    Stack = List[Dict[str, Union[str, Period]]]


class FullTracer:

    _simple_tracer: tracers.SimpleTracer
    _trees: list
    _current_node: Optional[tracers.TraceNode]

    def __init__(self) -> None:
        self._simple_tracer = tracers.SimpleTracer()
        self._trees = []
        self._current_node = None

    def record_calculation_start(
        self,
        variable: str,
        period: Period,
        branch_name: str = "default",
    ) -> None:
        self._simple_tracer.record_calculation_start(
            variable, period, branch_name
        )
        self._enter_calculation(variable, period, branch_name)
        self._record_start_time()

    def _enter_calculation(
        self,
        variable: str,
        period: Period,
        branch_name: str = "default",
    ) -> None:
        new_node = tracers.TraceNode(
            name=variable,
            period=period,
            parent=self._current_node,
            branch_name=branch_name,
        )

        if self._current_node is None:
            self._trees.append(new_node)

        else:
            self._current_node.append_child(new_node)

        self._current_node = new_node

    def record_parameter_access(
        self,
        parameter: str,
        period: Period,
        branch_name: str,
        value: ArrayLike,
    ) -> None:

        if self._current_node is not None:
            self._current_node.parameters.append(
                tracers.TraceNode(
                    name=parameter,
                    period=period,
                    branch_name=branch_name,
                    value=value,
                ),
            )

    def _record_start_time(
        self,
        time_in_s: Optional[float] = None,
    ) -> None:
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        if self._current_node is not None:
            self._current_node.start = time_in_s

    def record_calculation_result(self, value: ArrayLike) -> None:
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
    def trees(self) -> List[tracers.TraceNode]:
        return self._trees

    @property
    def computation_log(self) -> tracers.ComputationLog:
        return tracers.ComputationLog(self)

    @property
    def performance_log(self) -> tracers.PerformanceLog:
        return tracers.PerformanceLog(self)

    @property
    def flat_trace(self) -> tracers.FlatTrace:
        return tracers.FlatTrace(self)

    def _get_time_in_sec(self) -> float:
        return time.time_ns() / (10**9)

    def print_computation_log(self, aggregate=False, max_depth=None):
        self.computation_log.print_log(aggregate, max_depth)

    def generate_performance_graph(self, dir_path: str) -> None:
        self.performance_log.generate_graph(dir_path)

    def generate_performance_tables(self, dir_path: str) -> None:
        self.performance_log.generate_performance_tables(dir_path)

    def _get_nb_requests(self, tree: tracers.TraceNode, variable: str) -> int:
        tree_call = tree.name == variable
        children_calls = sum(
            self._get_nb_requests(child, variable) for child in tree.children
        )

        return tree_call + children_calls

    def get_nb_requests(self, variable: str) -> int:
        return sum(
            self._get_nb_requests(tree, variable) for tree in self.trees
        )

    def get_flat_trace(self) -> dict:
        return self.flat_trace.get_trace()

    def get_serialized_flat_trace(self) -> dict:
        return self.flat_trace.get_serialized_trace()

    def browse_trace(self) -> Iterator[tracers.TraceNode]:
        def _browse_node(node):
            yield node

            for child in node.children:
                yield from _browse_node(child)

        for node in self._trees:
            yield from _browse_node(node)
