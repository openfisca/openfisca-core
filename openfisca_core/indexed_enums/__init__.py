"""Enumerations for variables with a limited set of possible values."""

from . import types
from ._enum_type import EnumType
from ._errors import EnumMemberNotFoundError
from .config import ENUM_ARRAY_DTYPE
from .enum import Enum
from .enum_array import EnumArray

__all__ = [
    "ENUM_ARRAY_DTYPE",
    "Enum",
    "EnumArray",
    "EnumMemberNotFoundError",
    "EnumType",
    "types",
]
