from __future__ import annotations

import typing
from typing import Union

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from openfisca_core.periods import Period

    Stack = list[dict[str, Union[str, Period]]]


class SimpleTracer:
    _stack: Stack

    def __init__(self) -> None:
        self._stack = []

    def record_calculation_start(self, variable: str, period: Period | int) -> None:
        self.stack.append({"name": variable, "period": period})

    def record_calculation_result(self, value: ArrayLike) -> None:
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value) -> None:
        pass

    def record_calculation_end(self) -> None:
        self.stack.pop()

    @property
    def stack(self) -> Stack:
        return self._stack
