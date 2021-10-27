from __future__ import annotations

from typing import Any, Sequence, Mapping
from typing_extensions import TypedDict


class _TestSchema(TypedDict, total = False):
    absolute_error_margin: float
    extensions: Sequence[str]
    input: Mapping[str, Mapping[str, Any]]
    keywords: Sequence[str]
    max_spiral_loops: int
    name: str
    output: Mapping[str, Mapping[str, Any]]
    period: str
    reforms: Sequence[str]
    relative_error_margin: float
