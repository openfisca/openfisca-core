from __future__ import annotations

from typing import Optional, Sequence, Union

from pydantic import BaseModel


class Axes(BaseModel):
    parallel: Sequence[Axis] = []
    perpendicular: Sequence[Axis] = []


class Axis(BaseModel):
    name: str
    count: int
    min: float
    max: float
    index: int
    period: Optional[Union[int, str]]
