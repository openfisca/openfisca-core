from __future__ import annotations

from typing import Optional, Sequence
from typing_extensions import TypedDict


class _TestSchema(TypedDict):
    name: str
    keywords: Optional[Sequence[str]]
