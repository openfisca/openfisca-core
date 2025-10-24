from __future__ import annotations

import sys

import numpy

from openfisca_core import types as t
from openfisca_core.indexed_enums import EnumArray


class ComputationLog:
    _full_tracer: t.FullTracer

    def __init__(self, full_tracer: t.FullTracer) -> None:
        self._full_tracer = full_tracer

    def lines(
        self,
        aggregate: bool = False,
        max_depth: int = sys.maxsize,
    ) -> list[str]:
        depth = 1

        lines_by_tree = [
            self._get_node_log(node, depth, aggregate, max_depth)
            for node in self._full_tracer.trees
        ]

        return self._flatten(lines_by_tree)

    def print_log(self, aggregate: bool = False, max_depth: int = sys.maxsize) -> None:
        """Print the computation log of a simulation.

        If ``aggregate`` is ``False`` (default), print the value of each
        computed vector.

        If ``aggregate`` is ``True``, only print the minimum, maximum, and
        average value of each computed vector.

        This mode is more suited for simulations on a large population.

        If ``max_depth`` is ``sys.maxsize`` (default), print the entire
        computation.

        If ``max_depth`` is set, for example to ``3``, only print computed
        vectors up to a depth of ``max_depth``.
        """
        for line in self.lines(aggregate, max_depth):
            print(line)  # noqa: T201

    def _get_node_log(
        self,
        node: t.TraceNode,
        depth: int,
        aggregate: bool,
        max_depth: int = sys.maxsize,
    ) -> list[str]:
        if depth > max_depth:
            return []

        node_log = [self._print_line(depth, node, aggregate)]

        children_logs = [
            self._get_node_log(child, depth + 1, aggregate, max_depth)
            for child in node.children
        ]

        return node_log + self._flatten(children_logs)

    def _print_line(self, depth: int, node: t.TraceNode, aggregate: bool) -> str:
        indent = "  " * depth
        value = node.value

        if value is None:
            formatted_value = "{'avg': '?', 'max': '?', 'min': '?'}"

        elif aggregate:
            try:
                formatted_value = str(  # pyright: ignore[reportCallIssue]
                    {
                        "avg": numpy.mean(
                            value
                        ),  # pyright: ignore[reportArgumentType,reportCallIssue]
                        "max": numpy.max(value),
                        "min": numpy.min(value),
                    },
                )

            except TypeError:
                formatted_value = "{'avg': '?', 'max': '?', 'min': '?'}"

        else:
            formatted_value = self.display(value)

        return f"{indent}{node.name}<{node.period}> >> {formatted_value}"

    @staticmethod
    def display(value: t.VarArray, max_depth: int = sys.maxsize) -> str:
        if isinstance(value, EnumArray):
            value = value.decode_to_str()
        return numpy.array2string(value, max_line_width=max_depth)

    @staticmethod
    def _flatten(lists: list[list[str]]) -> list[str]:
        return [item for list_ in lists for item in list_]


__all__ = ["ComputationLog"]
