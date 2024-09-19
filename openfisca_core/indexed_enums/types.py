from __future__ import annotations

from openfisca_core.types import Array as Array
from openfisca_core.types import ArrayAny as ArrayAny  # noqa: F401
from openfisca_core.types import ArrayBool as ArrayBool  # noqa: F401
from openfisca_core.types import ArrayBytes as ArrayBytes  # noqa: F401
from openfisca_core.types import ArrayEnum as ArrayEnum
from openfisca_core.types import ArrayInt as ArrayInt  # noqa: F401
from openfisca_core.types import ArrayStr as ArrayStr  # noqa: F401

import abc
import enum

# Indexed enums


class Enum(enum.Enum):
    index: int


class EnumArray(Array[ArrayEnum], metaclass=abc.ABCMeta):
    ...
