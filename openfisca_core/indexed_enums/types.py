from typing import Protocol

from openfisca_core.types import Array, ArrayBytes, ArrayEnum, ArrayInt, ArrayStr

# Indexed enums


class Enum(Protocol):
    @classmethod
    def encode(cls, array: object) -> object:
        ...


__all__ = ["Array", "ArrayEnum", "ArrayStr", "ArrayBytes", "ArrayInt"]
