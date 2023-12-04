from __future__ import annotations

from typing import TypedDict


class AxisParams(TypedDict, total=False):
    name: str
    count: int
    min: float
    max: float
    period: str | int
    index: int
