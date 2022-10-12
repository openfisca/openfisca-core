from __future__ import annotations

import typing
from typing import List, Optional, Union

import numpy

from .. import tracers
from openfisca_core.indexed_enums import EnumArray

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    Array = Union[EnumArray, ArrayLike]


class ComputationLog:

    _full_tracer: tracers.FullTracer

    def __init__(self, full_tracer: tracers.FullTracer) -> None:
        self._full_tracer = full_tracer

    def display(
            self,
            value: Optional[Array],
            ) -> str:
        if isinstance(value, EnumArray):
            value = value.decode_to_str()

        return numpy.array2string(value, max_line_width = float("inf"))

    def lines(
            self,
            aggregate: bool = False,
            max_depth: Optional[int] = None,
            ) -> List[str]:
        depth = 1

        lines_by_tree = [
            self._get_node_log(node, depth, aggregate, max_depth)
            for node
            in self._full_tracer.trees
            ]

        return self._flatten(lines_by_tree)

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
            node: tracers.TraceNode,
            depth: int,
            aggregate: bool,
            max_depth: Optional[int],
            ) -> List[str]:

        if max_depth is not None and depth > max_depth:
            return []

        node_log = [self._print_line(depth, node, aggregate, max_depth)]

        children_logs = [
            self._get_node_log(child, depth + 1, aggregate, max_depth)
            for child
            in node.children
            ]

        return node_log + self._flatten(children_logs)

    def _print_line(
            self,
            depth: int,
            node: tracers.TraceNode,
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

    def _flatten(
            self,
            lists: List[List[str]],
            ) -> List[str]:
        return [item for list_ in lists for item in list_]
