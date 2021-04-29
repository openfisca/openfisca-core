import typing

import numpy

from openfisca_core.indexed_enums import EnumArray


class ComputationLog:

    def __init__(self, full_tracer):
        self._full_tracer = full_tracer

    def display(self, value):
        if isinstance(value, EnumArray):
            value = value.decode_to_str()

        return numpy.array2string(value, max_line_width = float("inf"))

    def _get_node_log(self, node, depth, aggregate) -> typing.List[str]:

        def print_line(depth, node) -> str:
            value = node.value
            if aggregate:
                try:
                    formatted_value = str({'avg': numpy.mean(value), 'max': numpy.max(value), 'min': numpy.min(value)})
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

    def lines(self, aggregate = False) -> typing.List[str]:
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
