from __future__ import annotations

from typing import Sequence
from openfisca_core.types import ArrayLike, FrameSchema, PeriodType

Stack = Sequence[FrameSchema]


class SimpleTracer:

    _stack: Stack

    def __init__(self) -> None:
        self._stack = []

    def record_calculation_start(
            self,
            variable: str,
            period: PeriodType,
            ) -> None:

        frame: FrameSchema
        frame = {'name': variable, 'period': period}
        self.stack = [*self.stack, frame]

    def record_calculation_result(self, value: ArrayLike) -> None:
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value):
        pass

    def record_calculation_end(self) -> None:
        self.stack = self.stack[:-1]

    @property
    def stack(self) -> Stack:
        return self._stack

    @stack.setter
    def stack(self, value: Stack) -> None:
        self._stack = value
