from __future__ import annotations

from typing import Dict

import collections
import dataclasses

from openfisca_core import types


@dataclasses.dataclass(frozen = True)
class Files(collections.UserDict):
    data: Dict[types.Period, str]
