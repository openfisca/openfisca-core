from __future__ import annotations

from typing import Optional, Sequence
from typing_extensions import TypedDict


class RoleSchema(TypedDict, total = False):
    """Data-schema for :class:`.Role`.

    .. versionadded:: 35.8.0

    """

    key: str
    plural: Optional[str]
    label: Optional[str]
    doc: Optional[str]
    max: Optional[int]
    subroles: Optional[Sequence[str]]
