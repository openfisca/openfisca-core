from __future__ import annotations

import sys

import numpy

from openfisca_core import types as t
from openfisca_core.indexed_enums import Enum, EnumArray


class ComputationLog:
    _full_tracer: t.FullTracer

    def __init__(self, full_tracer: t.FullTracer) -> None:
        self._full_tracer = full_tracer

    def lines(
        self,
        aggregate: bool = False,
        max_depth: int = sys.maxsize,
        ignore_default: bool = False,
        tax_benefit_system: t.TaxBenefitSystem | None = None,
    ) -> list[str]:
        """Generate lines for the computation log.

        Args:
            aggregate: Show aggregated statistics instead of individual values.
            max_depth: Maximum depth to display in the computation tree.
            ignore_default: Hide variables with default values and their children.
            tax_benefit_system: Used to get default values for variables.

        Returns:
            List of strings representing the computation log lines.

        """
        depth = 1

        lines_by_tree = [
            self._get_node_log(
                node, depth, aggregate, max_depth, ignore_default, tax_benefit_system
            )
            for node in self._full_tracer.trees
        ]

        return self._flatten(lines_by_tree)

    def print_log(
        self,
        aggregate: bool = False,
        max_depth: int = sys.maxsize,
        ignore_default: bool = False,
        tax_benefit_system: t.TaxBenefitSystem | None = None,
    ) -> None:
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

        If ``ignore_default`` is ``True``, do not display variables that have
        their default value. When a variable with its default value is hidden,
        its children are also hidden, even if they have non-default values.
        """
        for line in self.lines(
            aggregate, max_depth, ignore_default, tax_benefit_system
        ):
            print(line)  # noqa: T201

    def _get_node_log(
        self,
        node: t.TraceNode,
        depth: int,
        aggregate: bool,
        max_depth: int = sys.maxsize,
        ignore_default: bool = False,
        tax_benefit_system: t.TaxBenefitSystem | None = None,
    ) -> list[str]:
        if depth > max_depth:
            return []

        # Check if we should ignore this node because it has its default value
        if ignore_default and self._is_default_value(node, tax_benefit_system):
            # Don't display this node or its children
            return []

        node_log = [self._print_line(depth, node, aggregate)]

        children_logs = [
            self._get_node_log(
                child,
                depth + 1,
                aggregate,
                max_depth,
                ignore_default,
                tax_benefit_system,
            )
            for child in node.children
        ]

        return node_log + self._flatten(children_logs)

    def _is_default_value(
        self, node: t.TraceNode, tax_benefit_system: t.TaxBenefitSystem | None
    ) -> bool:
        """Check if a node's value is the default value for its variable.

        Args:
            node: The trace node to check
            tax_benefit_system: The tax benefit system to get variable information

        Returns:
            True if the value is the default value, False otherwise
        """
        if tax_benefit_system is None or node.value is None:
            return False

        try:
            variable = tax_benefit_system.get_variable(node.name)
            if variable is None:
                return False

            default_value = variable.default_value
            if default_value is None:
                return False

            # For arrays, check if all values equal the default
            if isinstance(node.value, numpy.ndarray):
                # Handle EnumArray specially
                if isinstance(node.value, EnumArray):
                    # For Enum, compare the enum values
                    if variable.value_type == Enum:
                        # Check if all values in the array are the default enum value
                        return numpy.all(node.value == default_value)
                    return False

                # For numeric/boolean arrays, check if all values equal default
                try:
                    return numpy.all(node.value == default_value)
                except (ValueError, TypeError):
                    # If comparison fails, assume not default
                    return False

            # For scalar values, direct comparison
            return node.value == default_value

        except Exception:
            # If we can't determine, assume not default to be safe
            return False

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
