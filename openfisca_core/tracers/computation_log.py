from __future__ import annotations

import typing

import numpy
import numpy.typing

from openfisca_core.indexed_enums import EnumArray

if typing.TYPE_CHECKING:
    from openfisca_core.tracers import FullTracer, TraceNode

    Array = typing.Union[EnumArray, numpy.typing.ArrayLike]


class ComputationLog:

    _full_tracer: FullTracer

    def __init__(self, full_tracer: FullTracer) -> None:
        self._full_tracer = full_tracer

    def display(
            self,
            value: typing.Optional[Array],
            ) -> str:
        if isinstance(value, EnumArray):
            value = value.decode_to_str()

        return numpy.array2string(value, max_line_width = float("inf"))

    def _get_node_log(
            self,
            node: TraceNode,
            depth: int,
            aggregate: bool,
            ) -> typing.List[str]:

        def print_line(depth: int, node: TraceNode) -> str:
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

        node_log = [print_line(depth, node)]

        children_logs = [
            self._get_node_log(child, depth + 1, aggregate)
            for child
            in node.children
            ]

        return node_log + self._flatten(children_logs)

    def _flatten(
            self,
            list_of_lists: typing.List[typing.List[str]],
            ) -> typing.List[str]:
        return [item for _list in list_of_lists for item in _list]

    def lines(self, aggregate: bool = False) -> typing.List[str]:
        depth = 1

        lines_by_tree = [
            self._get_node_log(node, depth, aggregate)
            for node
            in self._full_tracer.trees
            ]

        return self._flatten(lines_by_tree)

    def print_log(self, aggregate = False) -> None:
        """
        Print the computation log of a simulation.

        If ``aggregate`` is ``False`` (default), print the value of each
        computed vector.

        If ``aggregate`` is ``True``, only print the minimum, maximum, and
        average value of each computed vector.

        This mode is more suited for simulations on a large population.
        """
        for line in self.lines(aggregate):
            print(line)  # noqa T001
