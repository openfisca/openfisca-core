from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import numpy
    import numpy.typing

    from openfisca_core.periods import Period

    Stack = typing.List[typing.Dict[str, typing.Union[str, Period]]]


class SimpleTracer:

    _stack: Stack

    def __init__(self) -> None:
        self._stack = []

    def record_calculation_start(self, variable: str, period: Period) -> None:
        self.stack.append({'name': variable, 'period': period})

    def record_calculation_result(self, value: numpy.typing.ArrayLike) -> None:
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value):
        pass

    def record_calculation_end(self) -> None:
        self.stack.pop()

    @property
    def stack(self) -> Stack:
        return self._stack
