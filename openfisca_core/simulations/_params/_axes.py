from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel


class AxisParams(BaseModel):
    name: str
    count: int
    min: float
    max: float
    period: Optional[Union[int, str]] = None
