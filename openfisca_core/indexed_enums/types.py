from enum import _EnumDict as EnumDict
from typing import TypeAlias

from numpy import (
    bool_ as BoolDType,
)
from numpy import (
    generic as VarDType,
)
from numpy import (
    int32 as IntDType,
)
from numpy import (
    object_ as ObjDType,
)
from numpy import (
    str_ as StrDType,
)

from openfisca_core.types import Array, ArrayLike, DTypeLike, Enum, EnumArray, EnumType

from .config import ENUM_ARRAY_DTYPE as EnumDType

#: Type for enum indices arrays.
IndexArray: TypeAlias = Array[EnumDType]

#: Type for boolean arrays.
BoolArray: TypeAlias = Array[BoolDType]

#: Type for int arrays.
IntArray: TypeAlias = Array[IntDType]

#: Type for str arrays.
StrArray: TypeAlias = Array[StrDType]

#: Type for object arrays.
ObjArray: TypeAlias = Array[ObjDType]

#: Type for generic arrays.
VarArray: TypeAlias = Array[VarDType]

__all__ = [
    "ArrayLike",
    "DTypeLike",
    "Enum",
    "EnumArray",
    "EnumDict",
    "EnumType",
]
