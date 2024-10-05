"""Enumerations for variables with a limited set of possible values.

These include:
    * Highest academic level: high school, associate degree, bachelor's degree,
      master's degree, doctorate…
    * A household housing occupancy status: owner, tenant, free-lodger,
      homeless…
    * The main occupation of a person: employee, freelancer, retired, student,
      unemployed…
    * Etc.

"""

from . import types
from .config import ENUM_ARRAY_DTYPE
from .enum import Enum
from .enum_array import EnumArray

__all__ = [
    "ENUM_ARRAY_DTYPE",
    "Enum",
    "EnumArray",
    "types",
]
