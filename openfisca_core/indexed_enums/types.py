from typing_extensions import TypeAlias

from openfisca_core.types import (
    Array,
    ArrayLike,
    DTypeLike,
    Enum,
    EnumArray,
    EnumType,
    RecArray,
)

from enum import _EnumDict as EnumDict  # noqa: PLC2701

import numpy
from numpy import (
    bool_ as BoolDType,
    generic as AnyDType,
    int32 as IntDType,
    object_ as ObjDType,
    str_ as StrDType,
    uint8 as EnumDType,
)

#: Type for the non-vectorised list of enum items.
ItemList: TypeAlias = list[tuple[int, str, EnumType]]

#: Type for record arrays data type.
RecDType: TypeAlias = numpy.dtype[numpy.void]

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
AnyArray: TypeAlias = Array[AnyDType]

__all__ = [
    "ArrayLike",
    "DTypeLike",
    "Enum",
    "EnumArray",
    "EnumDict",
    "EnumType",
    "RecArray",
]
