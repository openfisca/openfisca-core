from typing_extensions import TypeAlias

from openfisca_core.types import Array, ArrayLike

from numpy import bool_ as BoolDType, float32 as FloatDType

#: Type representing an numpy array of float32.
FloatArray: TypeAlias = Array[FloatDType]

__all__ = ["Array", "ArrayLike", "BoolDType"]
