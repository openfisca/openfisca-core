from __future__ import annotations

from typing import Any, Optional, Sequence

import sys

import numpy

from openfisca_core import commons, types


class ComputationLog:
    _full_tracer: types.FullTracer

    def __init__(self, full_tracer: types.FullTracer) -> None:
        self._full_tracer = full_tracer

    def display(self, value: types.Array[Any]) -> str:
        if isinstance(value, types.EnumArray):
            value = value.decode_to_str()

        return numpy.array2string(value, max_line_width = sys.maxsize)

    def lines(
            self,
            aggregate: bool = False,
            max_depth: Optional[int] = None,
            ) -> Sequence[str]:
        depth = 1

        lines_by_tree = [
            self._get_node_log(node, depth, aggregate, max_depth)
            for node
            in self._full_tracer.trees
            ]

        return tuple(commons.flatten(lines_by_tree))

    def print_log(self, aggregate = False, max_depth = None) -> None:
        """
        Print the computation log of a simulation.

        If ``aggregate`` is ``False`` (default), print the value of each
        computed vector.

        If ``aggregate`` is ``True``, only print the minimum, maximum, and
        average value of each computed vector.

        This mode is more suited for simulations on a large population.

        If ``max_depth`` is ``None`` (default), print the entire computation.

        If ``max_depth`` is set, for example to ``3``, only print computed
        vectors up to a depth of ``max_depth``.
        """
        for line in self.lines(aggregate, max_depth):
            print(line)  # noqa T001

    def _get_node_log(
            self,
            node: types.TraceNode,
            depth: int,
            aggregate: bool,
            max_depth: Optional[int],
            ) -> Sequence[str]:

        node_log: Sequence[str]
        children_log: Sequence[Sequence[str]]

        if max_depth is not None and depth > max_depth:
            return []

        node_log = [self._print_line(depth, node, aggregate, max_depth)]

        children_logs = [
            self._get_node_log(child, depth + 1, aggregate, max_depth)
            for child
            in node.children
            ]

        return [*node_log, *commons.flatten(children_logs)]

    def _print_line(
            self,
            depth: int,
            node: types.TraceNode,
            aggregate: bool,
            max_depth: Optional[int],
            ) -> str:
        indent = '  ' * depth
        value = node.value

        if value is None:
            formatted_value = "{'avg': '?', 'max': '?', 'min': '?'}"

        elif aggregate:
            try:
                formatted_value = str({
                    'avg': numpy.mean(value),
                    'max': numpy.max(value),
                    'min': numpy.min(value),
                    })

            except TypeError:
                formatted_value = "{'avg': '?', 'max': '?', 'min': '?'}"

        else:
            formatted_value = self.display(value)

        return f"{indent}{node.name}<{node.period}> >> {formatted_value}"
