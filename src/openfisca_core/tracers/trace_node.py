from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    import numpy

    from openfisca_core.indexed_enums import EnumArray
    from openfisca_core.periods import Period

    Array = typing.Union[EnumArray, numpy.typing.ArrayLike]
    Time = typing.Union[float, int]


@dataclasses.dataclass
class TraceNode:
    name: str
    period: Period
    parent: typing.Optional[TraceNode] = None
    children: typing.List[TraceNode] = dataclasses.field(default_factory = list)
    parameters: typing.List[TraceNode] = dataclasses.field(default_factory = list)
    value: typing.Optional[Array] = None
    start: float = 0
    end: float = 0

    def calculation_time(self, round_: bool = True) -> Time:
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
    def round(time: Time) -> float:
        return float(f'{time:.4g}')  # Keep only 4 significant figures
