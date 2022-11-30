from __future__ import annotations

from typing import Dict, Type

import collections
import dataclasses

from openfisca_core import types


@dataclasses.dataclass(frozen = True)
class Enums(collections.UserDict):
    data: Dict[str, Type[types.Enum]]
