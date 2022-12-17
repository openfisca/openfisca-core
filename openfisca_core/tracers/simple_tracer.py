from __future__ import annotations

from numpy.typing import ArrayLike
from openfisca_core.periods.typing import Period
from typing import Dict, List, Union

Stack = List[Dict[str, Union[str, Period]]]


class SimpleTracer:

    _stack: Stack

    def __init__(self) -> None:
        self._stack = []

    def record_calculation_start(self, variable: str, period: Period) -> None:
        self.stack.append({'name': variable, 'period': period})

    def record_calculation_result(self, value: ArrayLike) -> None:
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value):
        pass

    def record_calculation_end(self) -> None:
        self.stack.pop()

    @property
    def stack(self) -> Stack:
        return self._stack
