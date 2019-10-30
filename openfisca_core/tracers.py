# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import time
import csv
from itertools import groupby
from dataclasses import dataclass, field

import numpy as np
from typing import List, Dict, Optional, Iterator, Any
import importlib.resources as pkg_resources

from openfisca_core.parameters import ParameterNodeAtInstant, VectorialParameterNodeAtInstant, ALLOWED_PARAM_TYPES
from openfisca_core.indexed_enums import EnumArray
from openfisca_core.periods import Period


class TracingParameterNodeAtInstant:

    def __init__(self, parameter_node_at_instant, tracer):
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer

    def __getattr__(self, key):
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __getitem__(self, key):
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(self, child, key):
        period = self.parameter_node_at_instant._instant_str
        if isinstance(child, (ParameterNodeAtInstant, VectorialParameterNodeAtInstant)):
            return TracingParameterNodeAtInstant(child, self.tracer)
        if not isinstance(key, str) or isinstance(self.parameter_node_at_instant, VectorialParameterNodeAtInstant):
            # In case of vectorization, we keep the parent node name as, for instance, rate[status].zone1 is best described as the value of "rate"
            name = self.parameter_node_at_instant._name
        else:
            name = '.'.join([self.parameter_node_at_instant._name, key])
        if isinstance(child, (np.ndarray,) + ALLOWED_PARAM_TYPES):
            self.tracer.record_parameter_access(name, period, child)
        return child


class SimpleTracer:

    def __init__(self):
        self._stack = []

    def record_calculation_start(self, variable: str, period):
        self.stack.append({'name': variable, 'period': period})

    def record_calculation_result(self, value: np.ndarray):
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value):
        pass

    def record_calculation_end(self):
        self.stack.pop()

    @property
    def stack(self):
        return self._stack


@dataclass
class TraceNode:
    name: str
    period: Period
    parent: Optional[TraceNode] = None
    children: List[TraceNode] = field(default_factory = list)
    parameters: List[TraceNode] = field(default_factory = list)
    value: np.ndarray = None
    start: float = 0
    end: float = 0

    def calculation_time(self, round_ = True):
        result = self.end - self.start
        if round_:
            return self.round(result)
        return result

    def formula_time(self):
        result = self.calculation_time(round_ = False) - sum(child.calculation_time(round_ = False) for child in self.children)
        return self.round(result)

    def append_child(self, node: TraceNode):
        self.children.append(node)

    @staticmethod
    def round(time):
        return float(f'{time:.4g}')  # Keep only 4 significant figures


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

    def _record_start_time(self, time_in_s: Optional[float] = None):
        if time_in_s is None:
            time_in_s = self._get_time_in_sec()

        self._current_node.start = time_in_s

    def record_calculation_result(self, value: np.ndarray):
        self._current_node.value = value

    def record_calculation_end(self):
        self._simple_tracer.record_calculation_end()
        self._record_end_time()
        self._exit_calculation()

    def _record_end_time(self, time_in_s: Optional[float] = None):
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

    def browse_trace(self) -> Iterator[TraceNode]:
        def _browse_node(node):
            yield node
            for child in node.children:
                yield from _browse_node(child)

        for node in self._trees:
            yield from _browse_node(node)


class FlatTrace:

    def __init__(self, full_tracer):
        self._full_tracer = full_tracer

    def key(self, node: TraceNode) -> str:
        name = node.name
        period = node.period
        return f"{name}<{period}>"

    def get_trace(self):
        trace = {}
        for node in self._full_tracer.browse_trace():
            trace.update({  # We don't want cache read to overwrite data about the initial calculation. We therefore use a non-overwriting update.
                key: node_trace
                for key, node_trace in self._get_flat_trace(node).items()
                if key not in trace
                })
        return trace

    def get_serialized_trace(self):
        return {
            key: {
                **flat_trace,
                'value': self.serialize(flat_trace['value'])
                }
            for key, flat_trace in self.get_trace().items()
            }

    def serialize(self, value: np.ndarray) -> List:
        if isinstance(value, EnumArray):
            value = value.decode_to_str()
        if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.dtype(bytes)):
            value = value.astype(np.dtype(str))
        if isinstance(value, np.ndarray):
            value = value.tolist()
        return value

    def _get_flat_trace(self, node: TraceNode) -> Dict[str, Dict]:
        key = self.key(node)

        node_trace = {
            key: {
                'dependencies': [
                    self.key(child) for child in node.children
                    ],
                'parameters': {
                    self.key(parameter): self.serialize(parameter.value) for parameter in node.parameters
                    },
                'value': node.value,
                'calculation_time': node.calculation_time(),
                'formula_time': node.formula_time(),
                },
            }
        return node_trace


class ComputationLog:

    def __init__(self, full_tracer):
        self._full_tracer = full_tracer

    def display(self, value):
        if isinstance(value, EnumArray):
            value = value.decode_to_str()

        return np.array2string(value, max_line_width = float("inf"))

    def _get_node_log(self, node, depth, aggregate) -> List[str]:

        def print_line(depth, node) -> str:
            value = node.value
            if aggregate:
                try:
                    formatted_value = str({'avg': np.mean(value), 'max': np.max(value), 'min': np.min(value)})
                except TypeError:
                    formatted_value = "{'avg': '?', 'max': '?', 'min': '?'}"
            else:
                formatted_value = self.display(value)

            return "{}{}<{}> >> {}".format('  ' * depth, node.name, node.period, formatted_value)

        # if not self.trace.get(node):
        #     return print_line(depth, node, "Calculation aborted due to a circular dependency")

        node_log = [print_line(depth, node)]
        children_logs = self._flatten(
            self._get_node_log(child, depth + 1, aggregate)
            for child in node.children
            )

        return node_log + children_logs

    def _flatten(self, list_of_lists):
        return [item for _list in list_of_lists for item in _list]

    def lines(self, aggregate = False) -> List[str]:
        depth = 1
        lines_by_tree = [self._get_node_log(node, depth, aggregate) for node in self._full_tracer.trees]
        return self._flatten(lines_by_tree)

    def print_log(self, aggregate = False):
        """
            Print the computation log of a simulation.

            If ``aggregate`` is ``False`` (default), print the value of each computed vector.

            If ``aggregate`` is ``True``, only print the minimum, maximum, and average value of each computed vector.
            This mode is more suited for simulations on a large population.
        """
        for line in self.lines(aggregate):
            print(line)  # noqa T001


class PerformanceLog:

    def __init__(self, full_tracer):
        self._full_tracer = full_tracer

    def generate_graph(self, dir_path):
        with open(os.path.join(dir_path, 'performance_graph.html'), 'w') as f:
            template = pkg_resources.read_text('openfisca_core.scripts.assets', 'index.html')
            perf_graph_html = template.replace('{{data}}', json.dumps(self._json()))
            f.write(perf_graph_html)

    def generate_performance_tables(self, dir_path: str) -> None:

        flat_trace = self._full_tracer.get_flat_trace()

        csv_rows = [
            {'name': key, 'calculation_time': trace['calculation_time'], 'formula_time': trace['formula_time']}
            for key, trace in flat_trace.items()
            ]
        self._write_csv(os.path.join(dir_path, 'performance_table.csv'), csv_rows)

        aggregated_csv_rows = [
            {'name': key, **aggregated_time}
            for key, aggregated_time in self.aggregate_calculation_times(flat_trace).items()
            ]

        self._write_csv(os.path.join(dir_path, 'aggregated_performance_table.csv'), aggregated_csv_rows)

    def aggregate_calculation_times(self, flat_trace: Dict) -> Dict[str, Dict]:

        def _aggregate_calculations(calculations):
            calculation_count = len(calculations)
            calculation_time = sum(calculation[1]['calculation_time'] for calculation in calculations)
            formula_time = sum(calculation[1]['formula_time'] for calculation in calculations)
            return {
                'calculation_count': calculation_count,
                'calculation_time': TraceNode.round(calculation_time),
                'formula_time': TraceNode.round(formula_time),
                'avg_calculation_time': TraceNode.round(calculation_time / calculation_count),
                'avg_formula_time': TraceNode.round(formula_time / calculation_count),
                }

        all_calculations = sorted(flat_trace.items())
        return {
            variable_name: _aggregate_calculations(list(calculations))
            for variable_name, calculations in groupby(all_calculations, lambda calculation: calculation[0].split('<')[0])
            }

    def _json(self):
        children = [self._json_tree(tree) for tree in self._full_tracer.trees]
        calculations_total_time = sum(child['value'] for child in children)
        return {'name': 'All calculations', 'value': calculations_total_time, 'children': children}

    def _json_tree(self, tree: TraceNode):
        calculation_total_time = tree.calculation_time()
        children = [self._json_tree(child) for child in tree.children]
        return {'name': f"{tree.name}<{tree.period}>", 'value': calculation_total_time, 'children': children}

    def _write_csv(self, path: str, rows: List[Dict[str, Any]]) -> None:
        fieldnames = list(rows[0].keys())
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
