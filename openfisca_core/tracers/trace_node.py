from __future__ import annotations

from numpy.typing import ArrayLike
from typing import List

import dataclasses

from openfisca_core import periods
from openfisca_core.indexed_enums import EnumArray


@dataclasses.dataclass
class TraceNode:
    name: str
    period: periods.Period
    parent: TraceNode | None = None
    children: List[TraceNode] = dataclasses.field(default_factory = list)
    parameters: List[TraceNode] = dataclasses.field(default_factory = list)
    value: EnumArray | ArrayLike | None = None
    start: float = 0
    end: float = 0

    def calculation_time(self, round_: bool = True) -> float | int:
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
        self.children.append(node)

    @staticmethod
    def round(time: float | int) -> float:
        return float(f'{time:.4g}')  # Keep only 4 significant figures
