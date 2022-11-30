from __future__ import annotations

from typing import Dict

import collections
import dataclasses

import numpy

from openfisca_core import types


@dataclasses.dataclass(frozen = True)
class Arrays(collections.UserDict):
    data: Dict[types.Period, numpy.ndarray]
