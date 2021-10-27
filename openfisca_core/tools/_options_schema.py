from __future__ import annotations

from typing_extensions import TypedDict


class _OptionsSchema(TypedDict):
    ignore_variables: bool
    name_filter: bool
    only_variables: bool
    pdb: bool
    performance_graph: bool
    performance_tables: bool
    verbose: bool
