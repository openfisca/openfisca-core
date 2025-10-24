from typing_extensions import TypeAlias

from openfisca_core.types import Array, ArrayLike, DTypeLike, Enum, EnumArray, EnumType

from enum import _EnumDict as EnumDict  # noqa: PLC2701

from numpy import (
    bool_ as BoolDType,
    generic as VarDType,
    int32 as IntDType,
    object_ as ObjDType,
    str_ as StrDType,
    uint8 as EnumDType,
)

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
