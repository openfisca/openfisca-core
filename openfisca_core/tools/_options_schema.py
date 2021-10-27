from __future__ import annotations

from typing import Optional, Sequence
from typing_extensions import TypedDict


class _OptionsSchema(TypedDict, total = False):
    ignore_variables: Optional[Sequence[str]]
    name_filter: Optional[str]
    only_variables: Optional[Sequence[str]]
    pdb: bool
    performance_graph: bool
    performance_tables: bool
    verbose: bool
