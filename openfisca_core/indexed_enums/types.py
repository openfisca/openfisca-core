from typing import Protocol

from openfisca_core.types import (
    Array,
    ArrayAny,
    ArrayBool,
    ArrayBytes,
    ArrayEnum,
    ArrayInt,
    ArrayStr,
)

# Indexed enums


class Enum(Protocol):
    @classmethod
    def encode(cls, array: object) -> object:
        ...


class EnumArray(Protocol):
    ...


__all__ = [
    "Array",
    "ArrayAny",
    "ArrayBool",
    "ArrayEnum",
    "ArrayStr",
    "ArrayBytes",
    "ArrayInt",
]
