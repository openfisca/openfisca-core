from __future__ import annotations

from openfisca_core import types as t


class SimpleTracer:
    """A simple tracer that records a stack of traces."""

    #: The stack of traces.
    _stack: t.SimpleStack

    def __init__(self) -> None:
        self._stack = []

    @property
    def stack(self) -> t.SimpleStack:
        """Return the stack of traces."""
        return self._stack

    def record_calculation_start(
        self, variable: t.VariableName, period: t.PeriodInt | t.Period
    ) -> None:
        """Record the start of a calculation.

        Args:
            variable: The variable being calculated.
            period: The period for which the variable is being calculated.

        Examples:
            >>> from openfisca_core import tracers

            >>> tracer = tracers.SimpleTracer()
            >>> tracer.record_calculation_start("variable", 2020)
            >>> tracer.stack
            [{'name': 'variable', 'period': 2020}]

        """
        self.stack.append({"name": variable, "period": period})

    def record_calculation_result(self, value: t.ArrayLike[object]) -> None:
        """Ignore calculation result."""

    def record_parameter_access(
        self, parameter: str, period: t.Period, value: t.ArrayLike[object]
    ) -> None:
        """Ignore parameter access."""

    def record_calculation_end(self) -> None:
        """Record the end of a calculation.

        Examples:
            >>> from openfisca_core import tracers

            >>> tracer = tracers.SimpleTracer()
            >>> tracer.record_calculation_start("variable", 2020)
            >>> tracer.record_calculation_end()
            >>> tracer.stack
            []

        """
        self.stack.pop()


__all__ = ["SimpleTracer"]
