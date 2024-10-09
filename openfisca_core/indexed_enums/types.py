from typing_extensions import TypeAlias

from openfisca_core.types import (
    Array,
    ArrayLike,
    DTypeBool as BoolDType,
    DTypeEnum as EnumDType,
    DTypeGeneric as AnyDType,
    DTypeInt as IntDType,
    DTypeLike,
    DTypeObject as ObjDType,
    DTypeStr as StrDType,
    Enum,
    EnumArray,
    EnumType,
    RecArray,
)

import enum

import numpy

#: Type for enum dicts.
EnumDict: TypeAlias = enum._EnumDict  # noqa: SLF001

#: Type for the non-vectorised list of enum items.
ItemList: TypeAlias = list[tuple[int, str, Enum]]

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
    "Array",
    "ArrayLike",
    "BoolDType",
    "DTypeLike",
    "Enum",
    "EnumArray",
    "EnumType",
    "RecArray",
]
