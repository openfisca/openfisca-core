from __future__ import annotations

import dataclasses
import typing

import numpy

from openfisca_core.periods import Period


@dataclasses.dataclass
class TraceNode:
    name: str
    period: Period
    parent: typing.Optional[TraceNode] = None
    children: typing.List[TraceNode] = dataclasses.field(default_factory = list)
    parameters: typing.List[TraceNode] = dataclasses.field(default_factory = list)
    value: numpy.ndarray = None
    start: float = 0
    end: float = 0

    def calculation_time(self, round_ = True):
        result = self.end - self.start
        if round_:
            return self.round(result)
        return result

    def formula_time(self):
        result = self.calculation_time(round_ = False) - sum(child.calculation_time(round_ = False) for child in self.children)
        return self.round(result)

    def append_child(self, node: TraceNode):
        self.children.append(node)

    @staticmethod
    def round(time):
        return float(f'{time:.4g}')  # Keep only 4 significant figures
