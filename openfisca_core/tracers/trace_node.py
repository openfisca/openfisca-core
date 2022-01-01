from __future__ import annotations

from typing import Union, Optional, Sequence
from openfisca_core.typing import ArrayLike, PeriodProtocol

import dataclasses

from openfisca_core.indexed_enums import EnumArray

Array = Union[EnumArray, ArrayLike]


@dataclasses.dataclass
class TraceNode:
    name: str
    period: PeriodProtocol
    parent: Optional[TraceNode] = None
    children: Sequence[TraceNode] = dataclasses.field(default_factory = list)
    parameters: Sequence[TraceNode] = dataclasses.field(default_factory = list)
    value: Optional[Array] = None
    start: float = 0
    end: float = 0

    def calculation_time(self, round_: bool = True) -> float:
        result = self.end - self.start

        if round_:
            return self.round(result)

        return result

    def formula_time(self) -> float:
        children_calculation_time = sum(
            child.calculation_time(round_ = False)
            for child
            in self.children
            )

        result = (
            + self.calculation_time(round_ = False)
            - children_calculation_time
            )

        return self.round(result)

    def append_child(self, node: TraceNode) -> None:
        self.children = [*self.children, node]

    @staticmethod
    def round(time: float) -> float:
        return float(f'{time:.4g}')  # Keep only 4 significant figures
