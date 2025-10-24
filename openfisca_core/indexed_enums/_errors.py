from __future__ import annotations

from . import types as t


class EnumEncodingError(TypeError):
    """Raised when an enum is encoded with an unsupported type."""

    def __init__(
        self, enum_class: type[t.Enum], value: t.VarArray | t.ArrayLike[object]
    ) -> None:
        msg = (
            f"Failed to encode \"{value}\" of type '{value[0].__class__.__name__}', "
            "as it is not supported. Please, try again with an array of "
            f"'{int.__name__}', '{str.__name__}', or '{enum_class.__name__}'."
        )
        super().__init__(msg)


class EnumMemberNotFoundError(IndexError):
    """Raised when a member is not found in an enum."""

    def __init__(self, enum_class: type[t.Enum]) -> None:
        index = [str(enum.index) for enum in enum_class]
        names = [enum.name for enum in enum_class]
        msg = (
            f"Some members were not found in enum '{enum_class.__name__}'. "
            f"Possible values are: {', '.join(names[:-1])}, and {names[-1]!s}; "
            f"or their corresponding indices: {', '.join(index[:-1])}, and "
            f"{index[-1]}."
        )
        super().__init__(msg)


__all__ = ["EnumEncodingError", "EnumMemberNotFoundError"]
