import time
import typing

import numpy

# from openfisca_core import tracers
from openfisca_core.tracers import (
    ComputationLog,
    FlatTrace,
    PerformanceLog,
    SimpleTracer,
    TraceNode,
    )


class FullTracer:

    def __init__(self):
        self._simple_tracer = SimpleTracer()
        self._trees = []
        self._current_node = None

    def record_calculation_start(self, variable: str, period):
        self._simple_tracer.record_calculation_start(variable, period)
        self._enter_calculation(variable, period)
        self._record_start_time()

    def _enter_calculation(self, variable: str, period):
        new_node = TraceNode(name = variable, period = period, parent = self._current_node)
        if self._current_node is None:
            self._trees.append(new_node)
        else:
            self._current_node.append_child(new_node)
        self._current_node = new_node

    def record_parameter_access(self, parameter: str, period, value):
        self._current_node.parameters.append(TraceNode(name = parameter, period = period, value = value))

    def _record_start_time(self, time_in_s: typing.Optional[float] = None):
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        self._current_node.start = time_in_s

    def record_calculation_result(self, value: numpy.ndarray):
        self._current_node.value = value

    def record_calculation_end(self):
        self._simple_tracer.record_calculation_end()
        self._record_end_time()
        self._exit_calculation()

    def _record_end_time(self, time_in_s: typing.Optional[float] = None):
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        self._current_node.end = time_in_s

    def _exit_calculation(self):
        self._current_node = self._current_node.parent

    @property
    def stack(self):
        return self._simple_tracer.stack

    @property
    def trees(self):
        return self._trees

    @property
    def computation_log(self):
        return ComputationLog(self)

    @property
    def performance_log(self):
        return PerformanceLog(self)

    @property
    def flat_trace(self):
        return FlatTrace(self)

    def _get_time_in_sec(self) -> float:
        return time.time_ns() / (10**9)

    def print_computation_log(self, aggregate = False):
        self.computation_log.print_log(aggregate)

    def generate_performance_graph(self, dir_path: str) -> None:
        self.performance_log.generate_graph(dir_path)

    def generate_performance_tables(self, dir_path: str) -> None:
        self.performance_log.generate_performance_tables(dir_path)

    def _get_nb_requests(self, tree, variable: str):
        tree_call = tree.name == variable
        children_calls = sum(self._get_nb_requests(child, variable) for child in tree.children)

        return tree_call + children_calls

    def get_nb_requests(self, variable: str):
        return sum(self._get_nb_requests(tree, variable) for tree in self.trees)

    def get_flat_trace(self):
        return self.flat_trace.get_trace()

    def get_serialized_flat_trace(self):
        return self.flat_trace.get_serialized_trace()

    def browse_trace(self) -> typing.Iterator[TraceNode]:
        def _browse_node(node):
            yield node
            for child in node.children:
                yield from _browse_node(child)

        for node in self._trees:
            yield from _browse_node(node)
