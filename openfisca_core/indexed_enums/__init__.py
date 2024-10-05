"""Enumerations for variables with a limited set of possible values."""

from .config import ENUM_ARRAY_DTYPE
from .enum import Enum
from .enum_array import EnumArray
from . import types

__all__ = ["ENUM_ARRAY_DTYPE", "Enum", "EnumArray", "types"]
