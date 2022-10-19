from __future__ import annotations

import typing
from typing import Dict, List, Union

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from policyengine_core.periods import Period

    Stack = List[Dict[str, Union[str, Period]]]


class SimpleTracer:

    _stack: Stack

    def __init__(self) -> None:
        self._stack = []

    def record_calculation_start(
        self, variable: str, period: Period, branch_name: str = "default"
    ) -> None:
        self.stack.append(
            {"name": variable, "period": period, "branch_name": branch_name}
        )

    def record_calculation_result(self, value: ArrayLike) -> None:
        pass  # ignore calculation result

    def record_parameter_access(
        self, parameter: str, period, branch_name: str, value
    ):
        pass

    def record_calculation_end(self) -> None:
        self.stack.pop()

    @property
    def stack(self) -> Stack:
        return self._stack
