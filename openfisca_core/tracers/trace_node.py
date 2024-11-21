from __future__ import annotations

import dataclasses

from openfisca_core import types as t


@dataclasses.dataclass
class TraceNode:
    """A node in the tracing tree."""

    #: The name of the node.
    name: str

    #: The period of the node.
    period: t.PeriodInt | t.Period

    #: The parent of the node.
    parent: None | t.TraceNode = None

    #: The children of the node.
    children: list[t.TraceNode] = dataclasses.field(default_factory=list)

    #: The parameters of the node.
    parameters: list[t.TraceNode] = dataclasses.field(default_factory=list)

    #: The value of the node.
    value: None | t.VarArray = None

    #: The start time of the node.
    start: t.Time = 0.0

    #: The end time of the node.
    end: t.Time = 0.0

    def calculation_time(self, round_: bool = True) -> t.Time:
        """Calculate the time spent in the node.

        Args:
            round_: Whether to round the result.

        Returns:
            float: The time spent in the node.

        Examples:
            >>> from openfisca_core import tracers

            >>> node = tracers.TraceNode("variable", 2020)
            >>> node.start = 1.123122313
            >>> node.end = 1.12312313123

            >>> node.calculation_time()
            8.182e-07

            >>> node.calculation_time(round_=False)
            8.182299999770493e-07

        """
        result = self.end - self.start

        if round_:
            return self.round(result)

        return result

    def formula_time(self) -> t.Time:
        """Calculate the time spent on the formula.

        Returns:
            float: The time spent on the formula.

        Examples:
            >>> from openfisca_core import tracers

            >>> node = tracers.TraceNode("variable", 2020)
            >>> node.start = 1.123122313 * 11
            >>> node.end = 1.12312313123 * 11
            >>> child = tracers.TraceNode("variable", 2020)
            >>> child.start = 1.123122313
            >>> child.end = 1.12312313123

            >>> for i in range(10):
            ...     node.children = [child, *node.children]

            >>> node.formula_time()
            8.182e-07

        """
        children_calculation_time = sum(
            child.calculation_time(round_=False) for child in self.children
        )

        result = +self.calculation_time(round_=False) - children_calculation_time

        return self.round(result)

    def append_child(self, node: t.TraceNode) -> None:
        """Append a child to the node."""
        self.children.append(node)

    @staticmethod
    def round(time: t.Time) -> t.Time:
        """Keep only 4 significant figures.

        Args:
            time: The time to round.

        Returns:
            float: The rounded time.

        Examples:
            >>> from openfisca_core import tracers

            >>> tracers.TraceNode.round(0.000123456789)
            0.0001235

        """
        return float(f"{time:.4g}")


__all__ = ["TraceNode"]
