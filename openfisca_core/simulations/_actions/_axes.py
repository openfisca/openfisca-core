from __future__ import annotations

from typing import NamedTuple

from .._domain._axes import Axes, Axis
from .._params._axes import AxisParams


class AddParallelAxis(NamedTuple):
    axes: Axes

    def __call__(self, params: AxisParams) -> Axes:
        axis_params: AxisParams = AxisParams.parse_obj(params)
        index: int = len(self.axes.parallel)
        axis: Axis = Axis.parse_obj({"index": index, **dict(axis_params)})
        self.axes.parallel.append(axis)
        return self.axes


class AddPerpendicularAxis(NamedTuple):
    axes: Axes

    def __call__(self, params: AxisParams) -> Axes:
        axis_params: AxisParams = AxisParams.parse_obj(params)
        axis: Axis = Axis.parse_obj({"index": 0, **dict(axis_params)})
        self.axes.perpendicular.append(axis)
        return self.axes
