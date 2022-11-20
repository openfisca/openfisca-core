from __future__ import annotations

from typing import Dict, Optional, NamedTuple, Sequence, Union
from typing_extensions import Literal, TypedDict

import numpy

from ._domain import Period


class Cache(NamedTuple):
    variable: str
    period: Period

class Calculate(NamedTuple):
    variable: str
    period: Period
    option: Optional[Sequence[str]]


class MemoryUsage(TypedDict, total = False):
    by_variable: Dict[str, _MemoryUsageByVariable]
    total_nb_bytes: int


class _MemoryUsageByVariable(TypedDict, total = False):
    cell_size: int
    dtype: numpy.dtype
    nb_arrays: int
    nb_cells_by_array: int
    total_nb_bytes: int
